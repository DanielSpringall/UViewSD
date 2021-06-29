# Copyright 2021 by Daniel Springall.
# This file is part of UViewSD, and is released under the "MIT License Agreement".
# Please see the LICENSE file that should have been included as part of this package.
from uviewsd import shape
from uviewsd import uvwidget

from PySide2 import QtWidgets, QtCore, QtGui
from pxr import Usd, UsdGeom

import os
import logging

logger = logging.getLogger(__name__)


ICON_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "icons")


class UVViewerWindow(QtWidgets.QMainWindow):
    def __init__(self, stage=None, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent=parent)

        # Scene management
        self._stage = stage
        self._extractors = []
        self._availableUVSetNames = []

        # UI objects
        self._view = None
        self._gridToggleButton = None
        self._uvBorderHighlightToggleButton = None
        self._uvDataLabelButton = None
        self._uvSetNameComboBox = None
        self._uvNameLockCheckBox = None

        self.setWindowTitle("UViewSD")
        self._setupUI()
        self._setupConnections()
        self._view.setFocus()

    # UI
    def _setupUI(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(3)

        self._view = uvwidget.UVViewerWidget()

        layout.addLayout(self._setupControlLayout())
        layout.addWidget(self._view)

        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def _setupControlLayout(self):
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(3)

        uvOptionsLabel = QtWidgets.QLabel()
        uvOptionsLabel.setText("UV Set:")
        uvOptionsLabel.setFixedWidth(40)
        self._uvSetNameComboBox = QtWidgets.QComboBox()
        self._uvSetNameComboBox.setToolTip(
            "UV set name extracted from the selected USD prims."
        )
        self._uvSetNameComboBox.setMinimumWidth(200)

        spacerLine = QtWidgets.QFrame()
        spacerLine.setFrameShape(QtWidgets.QFrame.VLine)
        spacerLine.setFrameShadow(QtWidgets.QFrame.Sunken)

        self._gridToggleButton = QtWidgets.QPushButton()
        self._gridToggleButton.setIcon(QtGui.QIcon(os.path.join(ICON_DIR, "grid.png")))
        self._gridToggleButton.setFixedWidth(25)
        self._gridToggleButton.setToolTip(
            "Enable/disable visibility of the grid lines and numbers from the view."
        )

        self._uvBorderHighlightToggleButton = QtWidgets.QPushButton()
        self._uvBorderHighlightToggleButton.setIcon(
            QtGui.QIcon(os.path.join(ICON_DIR, "boundary.png"))
        )
        self._uvBorderHighlightToggleButton.setFixedWidth(25)
        self._uvBorderHighlightToggleButton.setToolTip(
            "Enable/disable highlight of uv boundary edges."
        )

        self._uvDataLabelButton = QtWidgets.QPushButton()
        self._uvDataLabelButton.setIcon(
            QtGui.QIcon(os.path.join(ICON_DIR, "uvdata.png"))
        )
        self._uvDataLabelButton.setFixedWidth(25)
        self._uvDataLabelButton.setToolTip(
            "Enable/disable display of mouse uv position."
        )

        layout.addWidget(uvOptionsLabel)
        layout.addWidget(self._uvSetNameComboBox)
        layout.addSpacing(3)
        layout.addWidget(spacerLine)
        layout.addSpacing(3)
        layout.addWidget(self._uvBorderHighlightToggleButton)
        layout.addWidget(self._gridToggleButton)
        layout.addWidget(self._uvDataLabelButton)
        return layout

    def _setupConnections(self):
        self._gridToggleButton.clicked.connect(self._view.toggleGridVisibility)
        self._uvBorderHighlightToggleButton.clicked.connect(
            self._view.toggleUVEdgeBoundaryHighlight
        )
        self._uvDataLabelButton.clicked.connect(self._view.toggleMouseUVPositionDisplay)
        self._uvSetNameComboBox.currentIndexChanged.connect(self.refreshUVViewer)

    def keyPressEvent(self, event):
        self._view.keyPressEvent(event)
        QtWidgets.QMainWindow.keyPressEvent(self, event)

    # UV NAME
    @staticmethod
    def defaultUVSetNameOrder():
        """Return a list of possible prim names to search for uv's with."""
        return ["uv", "st"]

    def setUVSetName(self, name):
        """
        Programatically set the uv set name to be used by the viewer. This will update the name in the UI,
        as well as refresh the shapes in the viewer to use the new uv set name.
        The name must exist in the list of avaiable uv set names for a change to occur.

        Args:
            name (str): The name of the UV set to change the viewer to.
        """
        if name not in self._availableUVSetNames:
            logger.error("%s is not an available uv name to set.", name)
            return

        currentIndex = self._uvSetNameComboBox.currentIndex()
        requiredIndex = self._availableUVSetNames.index(name)
        if currentIndex == requiredIndex:
            logger.debug("UV name already set to %s.", name)
            return

        self._uvSetNameComboBox.setCurrentIndex(requiredIndex)

    def uvSetName(self):
        """The current uv set name selected in the UI by the user."""
        return self._uvSetNameComboBox.currentText()

    # VIEWER MANAGEMENT
    def addPrimPaths(self, primPaths, replace=False):
        """Add a given list of prim paths to the viewer.
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
        """Add a list of usd prims to the viewer.

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
            self._availableUVSetNames = []
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
                    if uvName not in self._availableUVSetNames:
                        newUVNames = True
                        self._availableUVSetNames.append(uvName)
                self._extractors.append(extractor)
            extractors.append(extractor)
        if not extractors:
            return

        # Update the uv name list
        if newUVNames:
            self._availableUVSetNames.sort()
            currentUVName = self.uvSetName()
            if not currentUVName:
                # Fall back on the first default uv name that exists
                for uvName in self.defaultUVSetNameOrder():
                    if uvName in self._availableUVSetNames:
                        currentUVName = uvName
                        break
                # No default uv name exists. Fall back on the first name in the list.
                else:
                    currentUVName = self._availableUVSetNames[0]
            try:
                self._uvSetNameComboBox.blockSignals(True)
                self._uvSetNameComboBox.clear()
                for uvName in self._availableUVSetNames:
                    self._uvSetNameComboBox.addItem(uvName)
                self._uvSetNameComboBox.setCurrentIndex(
                    self._availableUVSetNames.index(currentUVName)
                )
            finally:
                self._uvSetNameComboBox.blockSignals(False)

        # Update the view
        shapeData = self.getShapeData(extractors)
        if shapeData:
            self._view.addShapes(shapeData)

    def getShapeData(self, extractors=None, uvName=None):
        """Get the relevant shape data to pass to the uv viewer from a list of extractors.

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
            uvName = self.uvSetName()
        if not extractors or not uvName:
            return {}

        shapeData = []
        for extractor in extractors:
            if not extractor.isUVNameValid(uvName):
                continue

            [positions, indices] = extractor.uvData(uvName)
            if positions is None or indices is None:
                continue

            identifier = extractor.prim().GetPath().pathString
            shapeData.append(shape.UVShape(positions, indices, identifier))
        return shapeData

    def refreshUVViewer(self):
        """Refresh the viewer with the current cache extractors, and uvName."""
        self._view.clear()
        shapeData = self.getShapeData()
        if shapeData:
            self._view.addShapes(shapeData)

    def setStage(self, stage):
        """Update and set a new stage for the viewer."""
        self._view.clear()
        self._stage = stage
        self._availableUVSetNames = []
        self._uvSetNameComboBox.blockSignals(True)
        self._uvSetNameComboBox.clear()
        self._uvSetNameComboBox.blockSignals(False)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseDesktopOpenGL)
    app = QtWidgets.QApplication([])

    stage = None
    primPaths = []

    # ATTIC
    # stage = Usd.Stage.Open("C:\\Libraries\\USD\\share\\usd\\Attic_NVIDIA\\Attic_NVIDIA.usd")
    # primPaths = ["/Root/Geometry/side_table_525/side_table"]

    # KITCHEN
    stage = Usd.Stage.Open(
        "C:\\Libraries\\USD\\share\\usd\\kitchenSet\\Kitchen_set.usd"
    )
    primPaths = [
        "/Kitchen_set/Props_grp/West_grp/WestWall_grp/FramePictureOval_1/Geom/FramePictureOval"
    ]

    # TESTS
    # stage = Usd.Stage.Open("C:\\Users\\Daniel\\Projects\\Python\\UViewSD\\uviewsd\\tests\\data\\uvborders.usda")
    # primPaths = ['/cube']

    window = UVViewerWindow(stage)
    window.addPrimPaths(primPaths)
    window.show()

    app.exec_()
