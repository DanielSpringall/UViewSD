import shape
import uvwidget

from PySide2 import QtWidgets, QtCore
from pxr import Usd, UsdGeom

import logging
logger = logging.getLogger(__name__)


class UVViewerWindow(QtWidgets.QMainWindow):
    def __init__(self, stage=None, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent=parent)

        # UI objects
        self._view = None
        self._gridToggleButton = None
        self._loadTextureButton = None
        self._toggleTextureButton = None
        self._textureOptionComboBox = None
        self._uvNameComboBox = None
        self._uvNameLockCheckBox = None

        # Scene management
        self._stage = stage
        self._extractors = []
        self._availableUVNames = []

        self._setupUI()
        self._setupConnections()

        self.setGeometry(850, 400, 800, 800)

    # UI
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
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(3)

        uvOptionsLabel = QtWidgets.QLabel()
        uvOptionsLabel.setText("UV:")
        uvOptionsLabel.setFixedWidth(20)
        self._uvNameComboBox = QtWidgets.QComboBox()
        self._uvNameComboBox.setMinimumWidth(50)

        spacerLine = QtWidgets.QFrame()
        spacerLine.setFrameShape(QtWidgets.QFrame.VLine)
        spacerLine.setFrameShadow(QtWidgets.QFrame.Sunken)

        self._gridToggleButton = QtWidgets.QPushButton()
        self._gridToggleButton.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, "SP_DialogSaveButton")))
        self._gridToggleButton.setFixedWidth(25)

        layout.addWidget(uvOptionsLabel)
        layout.addWidget(self._uvNameComboBox)
        layout.addSpacing(3)
        layout.addWidget(spacerLine)
        layout.addSpacing(3)
        layout.addWidget(self._gridToggleButton)
        return layout

    def _setupConnections(self):
        self._gridToggleButton.clicked.connect(self._view.toggleGridVisibility)
        self._uvNameComboBox.currentIndexChanged.connect(self.refreshUVViewer)

    def keyPressEvent(self, event):
        self._view.keyPressEvent(event)

    # UV NAME
    @staticmethod
    def defaultUVNameOrder():
        """ Return a list of possible prim names to search for uv's with. """
        return ["uv", "st"]

    def setUVName(self, uvName):
        """
        Programatically set the uvName to be used by the viewer. This will update the uvName in the UI, 
        as well as refresh the shapes in the viewer to use the new uv name.
        The uv name must exist in the list of avaiable uv names for a change to occur.

        Args:
            uvName (str): The name of the UV to set the viewer to.
        """
        if uvName not in self._availableUVNames:
            logger.error("%s is not an available uv name to set.", uvName)
            return

        currentIndex = self._uvNameComboBox.currentIndex()
        requiredIndex = self._availableUVNames.index(uvName)
        if currentIndex == requiredIndex:
            logger.debug("UV name already set to %s.", uvName)
            return

        self._uvNameComboBox.setCurrentIndex(requiredIndex)

    def uvName(self):
        """ The current uvName selected in the UI by the user. """
        return self._uvNameComboBox.currentText()

    # VIEWER MANAGEMENT
    def addPrimPaths(self, primPaths, replace=False):
        """ Add a given list of prim paths to the viewer.
        See addPrims for more information about how the specified.

        Args:
            primPaths (list[str]): List of prim paths to get from the stage and add to the view.
            replace (bool): If True, will clear the current uv's from the view before adding anything new.
        """
        if self._stage is None:
            logger.error("No stage set to extract prims from.")
            return
        prims = [self._stage.GetPrimAtPath(primPath) for primPath in primPaths]
        self.addPrims(prims, replace=replace)

    def addPrims(self, prims, replace=False):
        """ Add a list of usd prims to the viewer.

        Note, the current active uv name set in the UI is used to look for uv data.
        If replace is False, or the uv name is locked and no uv data exists with that name on any
        of the prim paths given, then there will be no percievable change to the UI.
        If however replace is True, and no uv data exists with the currently selected name, the available
        uv name list will be regenerated, and the most valid uvName found will be used.

        Args:
            prims (Usd.Prim): List of prims to get from the stage and add to the view.
            replace (bool): If True, will clear the current uv's from the view before adding anything new.
        """
        if replace:
            self._availableUVNames = []
            self._view.clear()

        # Get the valid extractors to use
        newUVNames = False
        extractors = []
        for prim in prims:
            if not prim.IsValid():
                logger.error("Invalid prim: %s", prim)
                continue
            extractor = None
            for extractor in self._extractors:
                if prim == extractor.prim():
                    break
            else:
                mesh = UsdGeom.Mesh(prim)
                if not shape.UVExtractor.validMesh(mesh):
                    logger.info("Invalid prim %s to extract uv data from.", prim)
                    continue
                extractor = shape.UVExtractor(mesh)
                for uvName in extractor.validUVNames():
                    if uvName not in self._availableUVNames:
                        newUVNames = True
                        self._availableUVNames.append(uvName)
                self._extractors.append(extractor)
            extractors.append(extractor)
        if not extractors:
            return

        # Update the uv name list
        if newUVNames:
            self._availableUVNames.sort()
            currentUVName = self.uvName()
            if not currentUVName:
                # Fall back on the first default uv name that exists
                for uvName in self.defaultUVNameOrder():
                    if uvName in self._availableUVNames:
                        currentUVName = uvName
                        break
                # No default uv name exists. Finally fall back on the first name in the list.
                else:
                    currentUVName = self._availableUVNames[0]
            try:            
                self._uvNameComboBox.blockSignals(True)
                self._uvNameComboBox.clear()
                for uvName in self._availableUVNames:
                    self._uvNameComboBox.addItem(uvName)
                self._uvNameComboBox.setCurrentIndex(self._availableUVNames.index(currentUVName))
            finally:
                self._uvNameComboBox.blockSignals(False)

        # Update the view
        shapeData = self.getShapeData(extractors)
        if shapeData:
            self._view.addShapes(shapeData)

    def refreshUVViewer(self):
        """ Refresh the viewer with the current cache extractors, and uvName. """
        self._view.clear()
        shapeData = self.getShapeData()
        if shapeData:
            self._view.addShapes(shapeData)

    def getShapeData(self, extractors=None, uvName=None):
        """ Get the relevant shape data to pass to the uv viewer from a list of extractors.

        Args:
            extractors (shape.UVExtractor | None):
                The extractors to get the shape data from. If no extractors are specified, will
                fall back on the cached extractors.
            uvName (str | None):
                The uv name of the data to extract. If none is specified, will fall back on the
                uv name specified in the UI by the user.
        Returns:
            dict{primPath: shape.UVShape}: Dictionary of shape data.
        """
        if extractors is None:
            extractors = self._extractors
        if uvName is None:
            uvName = self.uvName()
        if not extractors or not uvName:
            return {}

        shapeData = {}
        for extractor in extractors:
            if not extractor.isUVNameValid(uvName):
                continue

            [positions, indices] = extractor.uvData(uvName)
            if positions is None or indices is None:
                continue

            edges = []
            for edgeIndices in indices:
                for index in edgeIndices:
                    edges.extend(positions[index])
            shapeData[extractor.prim().GetPath().pathString] = shape.UVShape(edges)
        return shapeData

    def setStage(self, stage):
        """ Update and set a new stage for the viewer. """
        self._view.clear()
        self._stage = stage
        self._availableUVNames = []
        self._uvNameComboBox.blockSignals(True)
        self._uvNameComboBox.clear()
        self._uvNameComboBox.blockSignals(False)


def run():
    # stage = Usd.Stage.Open("C:\\Libraries\\USD\\share\\usd\\Attic_NVIDIA\\Attic_NVIDIA.usd")
    stage = Usd.Stage.Open("C:\\Libraries\\USD\\share\\usd\\kitchenSet\\Kitchen_set.usd")
    # stage = Usd.Stage.Open("C:\\Users\\Daniel\\Projects\\Python\\UViewSD\\tests\\uvdata.usda")
    parent = None

    window = UVViewerWindow(parent=parent, stage=stage)
    window.show()

    # ATTIC STUFF
    # primPath = "/Root/Geometry/side_table_525/side_table"
    # window.addPrimPaths([primPath])

    # KITCHEN STUFF
    window.addPrimPaths(['/Kitchen_set/Props_grp/North_grp/NorthWall_grp/CastIron_1/Geom/pCylinder151'])
    # window.addPrimPaths(['/root/faceVaryingUVs'])

    return window


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseDesktopOpenGL)
    app = QtWidgets.QApplication([])
    window = run()
    app.exec_()
