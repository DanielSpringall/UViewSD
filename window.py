from PySide2 import QtWidgets, QtCore
from pxr import Usd, UsdGeom

import shape
import logging
import uvwidget

logger = logging.getLogger(__name__)


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

        self._view = uvwidget.ViewerWidget()

        layout.addLayout(self._setupControlLayout())
        layout.addWidget(self._view)

        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def _setupControlLayout(self):
        controlLayout = QtWidgets.QHBoxLayout()
        controlLayout.setContentsMargins(3, 3, 3, 3)
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

        # textureLabel = QtWidgets.QLabel()
        # textureLabel.setText("Texture:")
        # textureLabel.setFixedWidth(40)
        # self._loadTextureButton = QtWidgets.QPushButton()
        # self._loadTextureButton.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, "SP_DialogOpenButton")))
        # self._loadTextureButton.setFixedWidth(25)
        # self._textureOptionComboBox = QtWidgets.QComboBox()
        # self._textureOptionComboBox.setMinimumWidth(50)
        # self._toggleTextureButton = QtWidgets.QPushButton()
        # self._toggleTextureButton.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, "SP_TitleBarNormalButton")))
        # self._toggleTextureButton.setFixedWidth(25)

        self._gridToggleButton = QtWidgets.QPushButton()
        self._gridToggleButton.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, "SP_DialogSaveButton")))
        self._gridToggleButton.setFixedWidth(25)

        controlLayout.addWidget(uvOptionsLabel)
        controlLayout.addWidget(self._uvOptionsComboBox)
        controlLayout.addWidget(self._uvNameLockButton)
        controlLayout.addSpacing(3)
        controlLayout.addWidget(spacerLine)
        controlLayout.addSpacing(3)
        # controlLayout.addWidget(textureLabel)
        # controlLayout.addWidget(self._loadTextureButton)
        # controlLayout.addWidget(self._textureOptionComboBox)
        # controlLayout.addWidget(self._toggleTextureButton)
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
