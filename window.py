from OpenGL import GL
from PySide2 import QtWidgets, QtGui, QtCore
import numpy as np
from pxr import Usd, UsdGeom

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
        self._background = None
        self._shapes = []
        self._camera = None

    def clear(self):
        # for shape in self._shapes:
            # Do something to shapes?
            # pass
        self._shapes = []

    def addShapes(self, shapes):
        if not isinstance(shapes, list):
            shapes = [shapes]
        self._shapes.extend(shapes)
        self.update()

    def removeShape(self):
        pass

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

    def addShape(self, shape):
        self._shapes.append(shape)
        self.update()

    def removeShape(self, shape):
        pass

    def initializeGL(self):
        self._background = shape.Grid()
        self._camera = camera.Camera2D(self.width(), self.height())
        self._painter = QtGui.QPainter()

    def resizeGL(self, width, height):
        GL.glViewport(0, 0, width, height)
        self._camera.resize(width, height)

    def paintGL(self):
        self._painter.begin(self)

        self._painter.beginNativePainting()
        GL.glClearColor(0.3, 0.3, 0.3, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        projectionMatrix = self._camera.glProjectionMatrix()
        self._background.draw(projectionMatrix)
        for shape in self._shapes:
            shape.draw(projectionMatrix)
        self._painter.endNativePainting()

        self.drawText(self._painter)
        self._painter.end()

    def drawText(self, painter):
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
        self._view = ViewerWidget()
        self.setCentralWidget(self._view)

        self.setGeometry(850, 400, 800, 800)

        self._usdviewApi = usdviewApi
        if usdviewApi:
            self._usdviewApi.dataModel.selection.signalPrimSelectionChanged.connect(self.selectionChanged)
        self._stage = stage

    def addPrimPaths(self, primPaths, override=False):
        prims = []
        for primPath in primPaths:
            prim = self._stage.GetPrimAtPath(primPath)
            if not prim.IsValid():
                logger.error("No valid prim at path: %s", primPath)
                continue
            prims.append(prim)
        return self.addPrims(prims, override)

    def addPrims(self, prims, override=False):
        if override:
            self._view.clear()

        shapes = []
        for prim in prims:
            shape = self._setupPrimShape(prim)
            if shape:
                shapes.append(shape)
            else:
                logger.warning("Unable to extract uv data from %s.", prim)
        self._view.addShapes(shapes)

    def keyPressEvent(self, event):
        self._view.keyPressEvent(event)
        if event.key() == QtCore.Qt.Key_R and self._usdviewApi:
            for path in self._usdviewApi.selectedPaths:
                self._view.clear()
                self.addPrimPath(path)

    def _setupPrimShape(self, prim, uvName="st"):
        mesh = UsdGeom.Mesh(prim)
        if not mesh:
            logger.warning("Invalid mesh prim \"%s\".", prim)

        faceVertCountAttr = mesh.GetFaceVertexCountsAttr()
        if not faceVertCountAttr:
            logger.warning("Missing face vertex count attribute on \"%s\"", prim)
            return None

        faceVertIndicesAttr = mesh.GetFaceVertexIndicesAttr()
        if not faceVertIndicesAttr:
            logger.warning("Missing face vertex indices attribute on \"%s\"", prim)
            return None

        uvPrimvar = mesh.GetPrimvar(uvName)
        if not UsdGeom.Primvar.IsPrimvar(uvPrimvar):
            logger.warning("Invalid primvar name \"%s\" on \"%s\".", uvName, prim)
            return None

        faceVertCountList = faceVertCountAttr.Get()
        uvValues = uvPrimvar.Get()
        uvIndices = uvPrimvar.GetIndices()
        faceVertexIndices = faceVertIndicesAttr.Get()

        interpolation = uvPrimvar.GetInterpolation()
        if interpolation == UsdGeom.Tokens.faceVarying:
            consumedIndices = 0
            uvLines = []
            for faceVertCount in faceVertCountList:
                lines = []
                for i in range(faceVertCount):
                    edgeStartIndex = consumedIndices + i
                    edgeEndIndex = consumedIndices if i  == (faceVertCount - 1) else edgeStartIndex + 1
                    lines.extend([uvValues[uvIndices[edgeStartIndex]], uvValues[uvIndices[edgeEndIndex]]])
                flattenedlines = [uv for uvData in lines for uv in uvData]
                uvLines.extend(flattenedlines)
                consumedIndices += faceVertCount
            return shape.UVShape(uvLines)
        elif interpolation == UsdGeom.Tokens.vertex:
            consumedIndices = 0
            uvLines = []
            for faceVertCount in faceVertCountList:
                lines = []
                for i in range(faceVertCount):
                    edgeStartIndex = consumedIndices + i
                    edgeEndIndex = consumedIndices if i  == (faceVertCount - 1) else edgeStartIndex + 1

                    edgeStartIndex = faceVertexIndices[edgeStartIndex]
                    edgeEndIndex = faceVertexIndices[edgeEndIndex]

                    lines.extend([uvValues[uvIndices[edgeStartIndex]], uvValues[uvIndices[edgeEndIndex]]])
                flattenedlines = [uv for uvData in lines for uv in uvData]
                uvLines.extend(flattenedlines)
                consumedIndices += faceVertCount
            return shape.UVShape(uvLines)

        raise RuntimeError("Invalid interpolation ({}) for uv data.".format(interpolation))

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
        stage = Usd.Stage.Open("C:\\Libraries\\USD\\share\\usd\\kitchenSet\\Kitchen_set.usd")
        parent = None

    window = Window(parent=parent, stage=stage, usdviewApi=usdviewApi)
    window.show()
    # primPath = "/Kitchen_set/Props_grp/North_grp/FridgeArea_grp/Refridgerator_1/Geom/Decorations/pPlane98"
    # primPath = "/Kitchen_set/Arch_grp/Kitchen_1/Geom/Sink_Curtain/nurbsToPoly22"
    # TODO: Work out why this prim fails to load
    if not usdviewApi:
        primPath = "/Kitchen_set/Arch_grp/Kitchen_1/Geom/TileFloor/pPlane215"
        window.addPrimPaths([primPath])
    # window.addPrimPath(primPath)

    return window


if __name__ == "__main__":
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseDesktopOpenGL)
    app = QtWidgets.QApplication([])
    window = run()
    app.exec_()
