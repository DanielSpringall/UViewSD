# Copyright 2021 by Daniel Springall.
# This file is part of UViewSD, and is released under the "MIT License Agreement".
# Please see the LICENSE file that should have been included as part of this package.
from uviewsd import sessionmanager
from uviewsd import viewerwidget

from PySide2 import QtWidgets, QtCore

import logging

logger = logging.getLogger(__name__)


class UViewSDWidget(QtWidgets.QWidget):
    """Main widget holding the viewer and its corresponding configuration elements."""

    def __init__(self, stage=None, config=None, parent=None):
        # Scene management
        self._sessionManager = sessionmanager.SessionManager(stage)

        # UI objects
        self._view = None
        self._gridToggleButton = None
        self._uvBorderHighlightToggleButton = None
        self._uvDataLabelToggleButton = None
        self._uvSetNameComboBox = None

        # Initialise UI
        QtWidgets.QWidget.__init__(self, parent=parent)
        self._config = config if config else UIConfiguration()
        self.setWindowTitle("UViewSD")
        self._setupUI()
        self._setupConnections()
        self._view.setFocus()

    # UI
    def _setupUI(self):
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(3)

        self._view = viewerwidget.UVViewerWidget(config=self._config, parent=self)

        if self._config.showViewerController:
            layout.addLayout(self._setupViewerControlLayout())
        layout.addWidget(self._view)

        self.setLayout(layout)

    def _setupViewerControlLayout(self):
        """Create and return a layout containing uv set combo box/options."""
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(5, 3, 5, 3)
        layout.setSpacing(3)

        if self._config.enableUVSetNameOption:
            uvOptionsLabel = QtWidgets.QLabel()
            uvOptionsLabel.setText("UV Set:")
            uvOptionsLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            self._uvSetNameComboBox = QtWidgets.QComboBox()
            toolTip = "UV set name extracted from the selected USD prims."
            self._uvSetNameComboBox.setToolTip(toolTip)
            self._uvSetNameComboBox.setMinimumWidth(200)
            self._uvSetNameComboBox.setSizePolicy(
                QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
            )

            spacerLine = QtWidgets.QFrame()
            spacerLine.setFrameShape(QtWidgets.QFrame.VLine)
            spacerLine.setFrameShadow(QtWidgets.QFrame.Sunken)
            layout.addWidget(uvOptionsLabel)
            layout.addWidget(self._uvSetNameComboBox)
            layout.addSpacing(3)
            layout.addWidget(spacerLine)
            layout.addSpacing(3)
        else:
            layout.addStretch()

        if self._config.enableUVBorderToggle:
            self._uvBorderHighlightToggleButton = QtWidgets.QCheckBox()
            self._uvBorderHighlightToggleButton.setText("UV Border")
            self._uvBorderHighlightToggleButton.setChecked(self._config.displayUVBorder)
            toolTip = "Enable/disable highlight of uv boundary edges."
            self._uvBorderHighlightToggleButton.setToolTip(toolTip)
            layout.addWidget(self._uvBorderHighlightToggleButton)

        if self._config.enableGridToggle:
            self._gridToggleButton = QtWidgets.QCheckBox()
            self._gridToggleButton.setText("Grid")
            self._gridToggleButton.setChecked(self._config.displayGrid)
            toolTip = (
                "Enable/disable visibility of the grid lines and numbers from the view."
            )
            self._gridToggleButton.setToolTip(toolTip)
            layout.addWidget(self._gridToggleButton)

        if self._config.enableUVPositionToggle:
            self._uvDataLabelToggleButton = QtWidgets.QCheckBox()
            self._uvDataLabelToggleButton.setText("UV Pos")
            self._uvDataLabelToggleButton.setChecked(
                self._view._showCurrentMouseUVPosition
            )
            toolTip = "Enable/disable display of mouse uv position."
            self._uvDataLabelToggleButton.setToolTip(toolTip)
            layout.addWidget(self._uvDataLabelToggleButton)

        return layout

    def _setupConnections(self):
        # Combo boxes
        if self._uvSetNameComboBox:
            self._uvSetNameComboBox.currentIndexChanged.connect(
                self.onUVSetNameSelected
            )

        # Toggle buttons
        if self._gridToggleButton:
            self._gridToggleButton.clicked.connect(
                lambda: self._view.setGridVisibility(self._gridToggleButton.isChecked())
            )
        if self._uvBorderHighlightToggleButton:
            self._uvBorderHighlightToggleButton.clicked.connect(
                lambda: self._view.setUVEdgeBoundaryHighlight(
                    self._uvBorderHighlightToggleButton.isChecked()
                )
            )
        if self._uvDataLabelToggleButton:
            self._uvDataLabelToggleButton.clicked.connect(
                lambda: self._view.setMouseUVPositionDisplay(
                    self._uvDataLabelToggleButton.isChecked()
                )
            )

    def keyPressEvent(self, event):
        self._view.keyPressEvent(event)
        QtWidgets.QMainWindow.keyPressEvent(self, event)

    # UV SET
    def setUVSetName(self, name):
        """
        Programatically set the uv set name to be used by the viewer. This will update the name in the UI,
        as well as refresh the shapes in the viewer to use the new uv set name.
        The name must exist in the list of avaiable uv set names for a change to occur.

        Args:
            name (str): The name of the UV set to change the viewer to.
        """
        changed = self._sessionManager.setActiveUVSetName(name)
        if changed:
            if self._uvSetNameComboBox:
                indexToSet = self._uvSetNameComboBox.findText(name)
                if indexToSet == -1:
                    logger.debug(
                        "UV set name combo box has become out of sync with session manager."
                    )
                    self._updateUvSetNameOptions()
                    try:
                        self._uvSetNameComboBox.blockSignals(True)
                        self._uvSetNameComboBox.setCurrentIndex(indexToSet)
                    finally:
                        self._uvSetNameComboBox.blockSignals(False)
            self.updateView(replace=True)

    def _updateUvSetNameOptions(self):
        """Update the uv set name combo box."""
        if not self._uvSetNameComboBox:
            return
        availableUVSetNames = self._sessionManager.availableUVSetNames()
        if not availableUVSetNames and self._uvSetNameComboBox.count() == 0:
            return
        activeUVSetName = self._sessionManager.activeUVSetName()

        # It's possible the user has selected a uv set name, then changed prim selection so that
        # there are no prims selected that have the current active uv set name.
        # It's on the user to update the option box to a valid uv set name in this use case.
        # So we need to add this name back into the list of names to add to the comb box.
        if activeUVSetName not in availableUVSetNames:
            availableUVSetNames.append(activeUVSetName)
            availableUVSetNames.sort()

        indexToSet = None
        if availableUVSetNames and activeUVSetName:
            indexToSet = availableUVSetNames.index(activeUVSetName)
        try:
            self._uvSetNameComboBox.blockSignals(True)
            self._uvSetNameComboBox.clear()
            for uvSetName in availableUVSetNames:
                self._uvSetNameComboBox.addItem(uvSetName)
            if indexToSet:
                self._uvSetNameComboBox.setCurrentIndex(indexToSet)
        finally:
            self._uvSetNameComboBox.blockSignals(False)

    def onUVSetNameSelected(self):
        """Triggered from user selection of the uv set name.

        If the new selection is not what is already in use, clear the view and
        update it with the new uv set data.
        """
        if not self._uvSetNameComboBox:
            return
        uvSetName = self._uvSetNameComboBox.currentText()
        changed = self._sessionManager.setActiveUVSetName(uvSetName)
        if changed:
            self.updateView(replace=True)

    # VIEWER MANAGEMENT
    def setStage(self, stage):
        """Set a new stage and update reset the viewer."""
        changed = self._sessionManager.setStage(stage)
        if changed:
            self.refreshView()

    def addPrimPaths(self, primPaths, replace=False):
        """Add a given list of prim paths to the viewer.

        Args:
            primPaths (list[str]): List of prim paths to get from the stage and add to the view.
            replace (bool): If True, will clear the current uv's from the view before adding anything new.
        """
        extractors = self._sessionManager.addPrimPaths(primPaths, replace)
        if extractors or replace:
            self._updateUvSetNameOptions()
            self.updateView(extractors=extractors, replace=replace)

    def addPrims(self, prims, replace=False):
        """Add a list of usd prims to the viewer.

        Args:
            prims (Usd.Prim): List of prims to get from the stage and add to the view.
            replace (bool): If True, will clear the current uv's from the view before adding anything new.
        """
        extractors = self._sessionManager.addPrims(prims, replace)
        if extractors or replace:
            self._updateUvSetNameOptions()
            self.updateView(extractors=extractors, replace=replace)

    def updateView(self, uvSetName=None, extractors=None, replace=False):
        """Update the view with new shape data.

        Args:
            uvSetName (str | None):
                The uv set name to use. If None, get the active uv set name from the session manager.
            extractors (list[shape.PrimUVDataExtractor] | None):
                A list of extractors to pull the shape data from. If None, get the list of
                cached extractors from the session manager.
            replace (bool): If True, will clear the current uv's from the view before adding anything new.
        """
        if replace:
            self._view.clear()
        shapeData = self._sessionManager.getShapeData(uvSetName, extractors)
        if shapeData:
            self._view.addShapes(shapeData)

    def refreshView(self):
        """Refresh the viewer with the current cache extractors and uvName."""
        self._view.clear()
        self._updateUvSetNameOptions()
        self.updateView()

    def clear(self):
        """Clear the viewer of any uvs currently drawn on the screen."""
        self._sessionManager.clear()
        self._view.clear()


class UIConfiguration(viewerwidget.ViewerConfiguration):
    """Class containing configuration for the UI layout and viewer setup."""

    def __init__(self):
        viewerwidget.ViewerConfiguration.__init__(self)

        # Overall toggle for any sort of user input configuration
        self.enableUserSettingOptions = True

        # Individual UI element configuration
        self.enableUVSetNameOption = True
        self.enableUVBorderToggle = True
        self.enableGridToggle = True
        self.enableUVPositionToggle = True

    @property
    def showViewerController(self):
        return self.enableUserSettingOptions and any(
            [
                self.enableUVSetNameOption,
                self.enableUVBorderToggle,
                self.enableGridToggle,
                self.enableUVPositionToggle,
            ]
        )
