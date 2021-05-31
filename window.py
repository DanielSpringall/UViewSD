from OpenGL.raw.GL.VERSION.GL_4_0 import GL_MAX_TESS_CONTROL_TOTAL_OUTPUT_COMPONENTS
from PySide2 import QtWidgets, QtGui, QtCore
from pxr import Usd, UsdGeom
from OpenGL import GL
import numpy as np

import shape
import states
import camera
import logging

logger = logging.getLogger(__name__)


class ViewerWidget(QtWidgets.QOpenGLWidget):
    def __init__(self, *args, **kwargs):
        QtWidgets.QOpenGLWidget.__init__(self, *args, **kwargs)

        self._painter = None
        self._activeState = None
        self._backgroundGrid = None
        self._shapes = {}
        self._camera = None
        self._showGrid = True

    def toggleGridVisibility(self):
        self._showGrid = not self._showGrid
        self.update()

    def removeAllShapes(self):
        if self._shapes:
            self._shapes = {}
            self.update()

    def addShapes(self, shapes):
        """ Add a list of shapes to be drawn in the scene and refresh the view. 
        
        Args:
            shapes (dict{name: shape.UVShape}):
                Dictionary of the shapes to draw. Keys are the identifiers for each shape, values are the shape data.
        """
        for shapeName in shapes:
            if shapeName in self._shapes:
                continue
            self._shapes[shapeName] = shapes[shapeName]
        self.update()

    def removeShapes(self, shapeNames):
        itemRemoved = False
        for shapeName in shapeNames:
            if shapeName not in self._shapes:
                continue
            del self._shapes[shapeName]
            itemRemoved = True

        if itemRemoved:
            self.update()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_F:
            self._camera.focus(0, 1, 1, 0)
            self.update()
        if event.key() == QtCore.Qt.Key_1:
            self._camera.zoom([0.5, 0.5], 0.9)
            self.update()
        if event.key() == QtCore.Qt.Key_2:
            self._camera.zoom([0.5, 0.5], 1.1)
            self.update()
        if event.key() == QtCore.Qt.Key_Left:
            self._camera.pan(-0.5, 0.0)
            self.update()
        if event.key() == QtCore.Qt.Key_Right:
            self._camera.pan(0.5, 0.0)
            self.update()
        if event.key() == QtCore.Qt.Key_Down:
            self._camera.pan(0.0, -0.5)
            self.update()
        if event.key() == QtCore.Qt.Key_Up:
            self._camera.pan(0.0, 0.5)
            self.update()

    def mousePressEvent(self, event):
        if not self._activeState:
            state = states.stateFromEvent(event)
            if state:
                self._activeState = state(event, self._camera, self.width(), self.height())

    def mouseMoveEvent(self, event):
        if self._activeState and self._activeState.update(event):
            self.update()

    def mouseReleaseEvent(self, event):
        if self._activeState and self._activeState.shouldDisable(event.button()):
            self._activeState = None

    def wheelEvent(self, event):
        if self._activeState:
            return

        pos = event.pos()
        screenCoords = [pos.x() / self.width(), pos.y() / self.height()]
        worldCoords = self._camera.mapScreenToWorld(screenCoords)
        delta = event.angleDelta().y()
        zoomAmount = 1 + (delta and delta // abs(delta)) * 0.03
        self._camera.zoom(worldCoords, zoomAmount)
        self.update()

    def initializeGL(self):
        """ Setup GL objects for the view ready for drawing. """
        self._backgroundGrid = shape.Grid()
        self._camera = camera.Camera2D(self.width(), self.height())
        self._painter = QtGui.QPainter()

    def resizeGL(self, width, height):
        """ Resize the GL viewport and update the camera with the new dimensions. """
        GL.glViewport(0, 0, width, height)
        self._camera.resize(width, height)

    def paintGL(self):
        """ Paint all the GL objects in the scene. """
        self._painter.begin(self)

        self._painter.beginNativePainting()
        GL.glClearColor(0.3, 0.3, 0.3, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        projectionMatrix = self._camera.glProjectionMatrix()
        if self._showGrid:
            self._backgroundGrid.draw(projectionMatrix)
        for shape in self._shapes.values():
            shape.draw(projectionMatrix)
        self._painter.endNativePainting()

        if self._showGrid:
            self.drawText(self._painter)
        self._painter.end()

    def drawText(self, painter):
        """ Pain the grid values in the scene. """
        screenCoord = [0.5, 0.5]

        originCoord = self._camera.mapWorldToScreen([0.0, 0.0])
        originCoord[0] = originCoord[0] * self.width()
        originCoord[1] = originCoord[1] * self.height()

        offsetCoord = self._camera.mapWorldToScreen([0.1, 0.1])
        offsetCoord[0] = offsetCoord[0] * self.width()
        offsetCoord[1] = offsetCoord[1] * self.height()

        width = offsetCoord[0] - originCoord[0]
        height = originCoord[1] - offsetCoord[1]
        doubleWidth = width * 2
        # Offset x a little to prevent intersection with the vertical grid line
        originX = originCoord[0] + width / 20
        originY = originCoord[1] - height

        def drawText(increment, xAxis=True):
            offset = float(increment) / 10
            if xAxis:
                left = originX + increment * width
                top = originY
            else:
                left = originX
                top = originY - increment * height

            text = str(offset)
            painter.drawText(left, top, doubleWidth, height, QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom, text)

        painter.setPen(QtCore.Qt.black)
        drawText(0)
        # Draw the rest of the text
        for i in range(1, shape.TOTAL_LINES + 1):
            drawText(i, xAxis=True)
            drawText(-i, xAxis=True)
            drawText(i, xAxis=False)
            drawText(-i, xAxis=False)


class Window(QtWidgets.QMainWindow):
    def __init__(self, parent, stage=None, usdviewApi=None, *args, **kwargs):
        QtWidgets.QMainWindow.__init__(self, parent=parent, *args, **kwargs)
        self._usdviewApi = usdviewApi
        self._stage = stage

        self._view = None
        self._gridToggleButton = None
        self._loadTextureButton = None
        self._toggleTextureButton = None
        self._textureOptionComboBox = None
        self._uvOptionsComboBox = None
        self._uvNameLockButton = None

        self._meshes = []

        self._setupUI()
        self._setupConnections()

        self.setGeometry(850, 400, 800, 800)

    def _setupUI(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(3)

        self._view = ViewerWidget()

        layout.addLayout(self._setupControlLayout())
        layout.addWidget(self._view)

        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def _setupControlLayout(self):
        controlLayout = QtWidgets.QHBoxLayout()
        controlLayout.setContentsMargins(0, 0, 0, 0)
        controlLayout.setSpacing(3)

        uvOptionsLabel = QtWidgets.QLabel()
        uvOptionsLabel.setText("UV:")
        uvOptionsLabel.setFixedWidth(20)
        self._uvOptionsComboBox = QtWidgets.QComboBox()
        self._uvOptionsComboBox.setMinimumWidth(50)
        self._uvNameLockButton = QtWidgets.QPushButton()
        self._uvNameLockButton.setFixedWidth(25)
        self._uvNameLockButton.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, "SP_MediaStop")))

        spacerLine = QtWidgets.QFrame()
        spacerLine.setFrameShape(QtWidgets.QFrame.VLine)
        spacerLine.setFrameShadow(QtWidgets.QFrame.Sunken)

        textureLabel = QtWidgets.QLabel()
        textureLabel.setText("Texture:")
        textureLabel.setFixedWidth(40)
        self._loadTextureButton = QtWidgets.QPushButton()
        self._loadTextureButton.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, "SP_DialogOpenButton")))
        self._loadTextureButton.setFixedWidth(25)
        self._textureOptionComboBox = QtWidgets.QComboBox()
        self._textureOptionComboBox.setMinimumWidth(50)
        self._toggleTextureButton = QtWidgets.QPushButton()
        self._toggleTextureButton.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, "SP_TitleBarNormalButton")))
        self._toggleTextureButton.setFixedWidth(25)

        self._gridToggleButton = QtWidgets.QPushButton()
        self._gridToggleButton.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, "SP_DialogSaveButton")))
        self._gridToggleButton.setFixedWidth(25)

        controlLayout.addWidget(uvOptionsLabel)
        controlLayout.addWidget(self._uvOptionsComboBox)
        controlLayout.addWidget(self._uvNameLockButton)
        controlLayout.addSpacing(3)
        controlLayout.addWidget(spacerLine)
        controlLayout.addSpacing(3)
        controlLayout.addWidget(textureLabel)
        controlLayout.addWidget(self._loadTextureButton)
        controlLayout.addWidget(self._textureOptionComboBox)
        controlLayout.addWidget(self._toggleTextureButton)
        controlLayout.addWidget(self._gridToggleButton)
        return controlLayout

    def _setupConnections(self):
        if self._usdviewApi:
            self._usdviewApi.dataModel.selection.signalPrimSelectionChanged.connect(self.selectionChanged)
        self._gridToggleButton.clicked.connect(self._view.toggleGridVisibility)

    def addPrimPaths(self, primPaths, replace=False):
        prims = []
        for primPath in primPaths:
            prim = self._stage.GetPrimAtPath(primPath)
            if not prim.IsValid():
                logger.error("No valid prim at path: %s", primPath)
                continue
            prims.append(prim)
        return self.addPrims(prims, replace=replace)

    def addPrims(self, prims, replace=False):
        if replace:
            self._view.clear()

        shapes = {}
        for prim in prims:
            for mesh in self._meshes:
                if prim == mesh.prim():
                    continue

            mesh = UsdGeom.Mesh(prim)
            if not shape.MeshUVs.validMesh(mesh):
                continue

            uvData = shape.MeshUVs(mesh)
            [positions, indices] = uvData.uvData("st")
            if positions is None or indices is None:
                continue

            lines = []
            for edgeIndices in indices:
                for index in edgeIndices:
                    lines.extend(positions[index])

            shapes[prim.GetPath().pathString] = shape.UVShape(lines)
        self._view.addShapes(shapes)

    def updateView(self):
        if not self._meshes:
            return

    def keyPressEvent(self, event):
        self._view.keyPressEvent(event)
        if event.key() == QtCore.Qt.Key_R and self._usdviewApi:
            for path in self._usdviewApi.selectedPaths:
                self._view.clear()
                self.addPrimPath(path)

    def selectionChanged(self, *args, **kwargs):
        selectedPaths = self._usdviewApi.selectedPaths
        if selectedPaths:
            self.addPrimPaths(selectedPaths, override=True)
        else:
            self._view.clear()


def run(usdviewApi=None, primPath=None):
    if usdviewApi:
        stage = usdviewApi.stage
        parent = usdviewApi.qMainWindow
    else:
        # stage = Usd.Stage.Open("C:\\Libraries\\USD\\share\\usd\\Attic_NVIDIA\\Attic_NVIDIA.usd")
        stage = Usd.Stage.Open("C:\\Libraries\\USD\\share\\usd\\kitchenSet\\Kitchen_set.usd")
        # stage = Usd.Stage.Open("C:\\Users\\Daniel\\Projects\\Python\\UViewSD\\tests\\uvdata.usda")
        parent = None

    window = Window(parent=parent, stage=stage, usdviewApi=usdviewApi)
    window.show()

    # ATTIC STUFF
    # if not usdviewApi:
        # primPath = "/Root/Geometry/side_table_525/side_table"
        # window.addPrimPaths([primPath])

    # KITCHEN STUFF
    if not usdviewApi:
        window.addPrimPaths(['/Kitchen_set/Props_grp/North_grp/NorthWall_grp/CastIron_1/Geom/pCylinder151'])
        # window.addPrimPaths(['/root/faceVaryingUVs'])

    return window


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseDesktopOpenGL)
    app = QtWidgets.QApplication([])
    window = run()
    app.exec_()
