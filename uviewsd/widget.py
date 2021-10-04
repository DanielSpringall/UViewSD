# Copyright 2021 by Daniel Springall.
# This file is part of UViewSD, and is released under the "MIT License Agreement".
# Please see the LICENSE file that should have been included as part of this package.
from uviewsd.core import sessionmanager as uc_sessionmanager
from uviewsd.core import usdextractor as uc_usdextractor
from uviewsd.ui import uvviewerwidget as ui_uvviewerwidget

from PySide2 import QtWidgets, QtCore

import logging

logger = logging.getLogger(__name__)


class Config:
    def __init__(self):
        # Global toggle for enabling/disabling the entire viewer configuration toolbar
        self.enableUserSettingOptions = True

        # Individual UI element configuration visibility
        self.enableUVSetNameOption = True
        self.enableUVBorderToggle = True
        self.enableGridToggle = True
        self.enableUVPositionToggle = True

        self.enableTextureDisplayToggle = True
        self.enableTextureRepeatToggle = True

        # Initial viewer configuration
        self.displayGrid = True
        self.displayUVPos = False
        self.displayUVBorder = False
        self.displayTexture = False
        self.textureRepeat = False

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


class UViewSDMixin(QtCore.QObject):
    def __init__(self, stage=None, config=None):
        """Main widget holding the uv viewer and its corresponding configuration elements."""
        if config is not None and not isinstance(config, Config):
            raise ValueError("Invalid config file passed to UViewSDWidget.")
        self._config = config if config else Config()

        # Scene management
        self._sessionManager = uc_sessionmanager.SessionManager(stage)

        # UI objects
        self._layout = None
        self._view = None
        self._gridToggleButton = None
        self._uvBorderHighlightToggleButton = None
        self._uvDataLabelToggleButton = None
        self._uvSetNameComboBox = None
        self._texturePathComboBox = None
        self._textureLoadButton = None
        self._textureDisplayToggleButton = None
        self._textureRepeatToggleButton = None
        # If the toolbar isn't enabled we need to track the enable/disable state of the uv edge borders
        self._displayUVBorder = self._config.displayUVBorder

        # Initialise UI
        self._setupUI()
        self._setupConnections()
        self._view.setFocus()

    # UI
    def _setupUI(self):
        self._layout = QtWidgets.QVBoxLayout()
        self._layout.setContentsMargins(3, 3, 3, 3)
        self._layout.setSpacing(3)
        self._view = ui_uvviewerwidget.UVViewerWidget(config=self._config, parent=self)
        if self._config.showViewerController:
            self._layout.addLayout(self._setupViewerControlLayout())
        if self._config.enableTextureDisplayToggle:
            self._layout.addLayout(self._setupTextureControlLayout())
        self._layout.addWidget(self._view)

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
            self._uvBorderHighlightToggleButton.setChecked(self._displayUVBorder)
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

    def _setupTextureControlLayout(self):
        """Create and return a layout containing texture combo box/options."""
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(5, 3, 5, 3)
        layout.setSpacing(3)

        textureLabel = QtWidgets.QLabel()
        textureLabel.setText("Texture:")
        textureLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self._texturePathComboBox = QtWidgets.QComboBox()
        self._texturePathComboBox.setToolTip("Texture path to display in the viewer.")
        self._texturePathComboBox.setMinimumWidth(200)
        self._texturePathComboBox.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )
        layout.addWidget(textureLabel)
        layout.addWidget(self._texturePathComboBox)

        self._textureLoadButton = QtWidgets.QPushButton()
        self._textureLoadButton.setIcon(
            self.style().standardIcon(getattr(QtWidgets.QStyle, "SP_DirOpenIcon"))
        )
        self._textureLoadButton.setFixedSize(25, 25)
        layout.addWidget(self._textureLoadButton)

        spacerLine = QtWidgets.QFrame()
        spacerLine.setFrameShape(QtWidgets.QFrame.VLine)
        spacerLine.setFrameShadow(QtWidgets.QFrame.Sunken)
        layout.addWidget(spacerLine)

        self._textureDisplayToggleButton = QtWidgets.QCheckBox()
        self._textureDisplayToggleButton.setText("Display Texture")
        self._textureDisplayToggleButton.setToolTip(
            "Enable/disable display of texture."
        )
        self._textureDisplayToggleButton.setChecked(self._view._showTexture)
        layout.addWidget(self._textureDisplayToggleButton)

        if self._config.enableTextureRepeatToggle:
            self._textureRepeatToggleButton = QtWidgets.QCheckBox()
            self._textureRepeatToggleButton.setText("Repeat")
            self._textureRepeatToggleButton.setToolTip(
                "Enable/disable repeat of the texture on the grid."
            )
            self._textureRepeatToggleButton.setChecked(self._config.textureRepeat)
            layout.addWidget(self._textureRepeatToggleButton)

        return layout

    def _setupConnections(self):
        # Combo boxes
        if self._uvSetNameComboBox is not None:
            self._uvSetNameComboBox.currentIndexChanged.connect(
                self._onUVSetNameSelected
            )
        if self._texturePathComboBox is not None:
            self._texturePathComboBox.currentIndexChanged.connect(
                self._onTextureSelected
            )

        # Toggle buttons
        if self._gridToggleButton is not None:
            self._gridToggleButton.clicked.connect(
                lambda: self._view.setGridVisibility(self._gridToggleButton.isChecked())
            )
        if self._uvDataLabelToggleButton is not None:
            self._uvDataLabelToggleButton.clicked.connect(
                lambda: self._view.setMouseUVPositionDisplay(
                    self._uvDataLabelToggleButton.isChecked()
                )
            )
        if self._uvBorderHighlightToggleButton is not None:
            self._uvBorderHighlightToggleButton.clicked.connect(
                lambda: self.displayUVBorders(
                    self._uvBorderHighlightToggleButton.isChecked()
                )
            )

        if self._textureDisplayToggleButton is not None:
            self._textureDisplayToggleButton.clicked.connect(self._onTextureToggled)
        if self._textureRepeatToggleButton:
            self._textureRepeatToggleButton.clicked.connect(
                lambda: self._view.setTextureRepeat(
                    self._textureRepeatToggleButton.isChecked()
                )
            )
        if self._textureLoadButton is not None:
            self._textureLoadButton.clicked.connect(self._openTexturePrompt)

    def keyPressEvent(self, event):
        self._view.keyPressEvent(event)

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
            if self._uvSetNameComboBox is not None:
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
            self.updateUVs(replace=True)

    def _updateUvSetNameOptions(self):
        """Update the uv set name combo box."""
        if self._uvSetNameComboBox is None:
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

    def _onUVSetNameSelected(self):
        """Triggered from user selection of the uv set name.

        If the new selection is not what is already in use, clear the view and
        update it with the new uv set data.
        """
        if self._uvSetNameComboBox is None:
            return
        uvSetName = self._uvSetNameComboBox.currentText()
        changed = self._sessionManager.setActiveUVSetName(uvSetName)
        if changed:
            self.updateUVs(replace=True)

    # TEXTURES
    def setTexturePath(self, path, enable=True):
        """
        Programatically set a texture path to be selected in the texture path combo box.
        If the texture display is currently active, the texture will be displayed in the view.

        Args:
            path (str): The texture path to add.
            enable (bool): If true, ensure the texture display is enabled to view the texture.
        """
        successful = self._sessionManager.setActiveTexturePath(path)
        if not successful:
            return
        self._updateTextureOptions()

        if enable:
            self._textureDisplayToggleButton.setChecked(True)
            self._view.setTextureVisible(True)
        if self._textureDisplayToggleButton.isChecked():
            self.updateTexture()

    def _updateTextureOptions(self):
        """Update the texture path combo box."""
        activeTexturePath = self._sessionManager.activeTexturePath()
        availableTexturePaths = self._sessionManager.availableTexturePaths()
        recentTexturePaths = self._sessionManager.recentTexturePaths()
        if (
            activeTexturePath in availableTexturePaths
            and activeTexturePath in recentTexturePaths
        ):
            availableTexturePaths.remove(activeTexturePath)

        allPaths = recentTexturePaths + availableTexturePaths
        if len(allPaths) == 0 and self._texturePathComboBox.count() == 0:
            return

        indexToSet = (
            allPaths.index(activeTexturePath)
            if allPaths and activeTexturePath
            else None
        )

        try:
            self._texturePathComboBox.blockSignals(True)
            self._texturePathComboBox.clear()

            for path in allPaths:
                self._texturePathComboBox.addItem(path)
            if recentTexturePaths and availableTexturePaths:
                self._texturePathComboBox.insertSeparator(len(recentTexturePaths))

            if indexToSet is not None:
                self._texturePathComboBox.setCurrentIndex(indexToSet)
            else:
                self._texturePathComboBox.insertItem(0, "")
                self._texturePathComboBox.setCurrentIndex(0)
        finally:
            self._texturePathComboBox.blockSignals(False)

    def _onTextureSelected(self):
        """Triggered from user selecting a texture path from the combo box."""
        path = self._texturePathComboBox.currentText()
        if not path:
            return
        self.setTexturePath(path, enable=True)

    def _onTextureToggled(self):
        """Triggered from user toggling texture visibility."""
        textureEnabled = self._textureDisplayToggleButton.isChecked()
        self._view.setTextureVisible(textureEnabled)
        if not textureEnabled:
            return
        self.updateTexture()

    def _openTexturePrompt(self):
        extensions = uc_usdextractor.VALID_IMAGE_EXTENSIONS
        filterString = "Image (*" + " *".join(extensions) + ")"
        fileToLoad = QtWidgets.QFileDialog.getOpenFileName(
            self, "Load Image", filter=filterString
        )
        if fileToLoad:
            self.setTexturePath(fileToLoad[0], enable=True)

    # VIEWER MANAGEMENT
    def setStage(self, stage):
        """Set a new stage and update reset the viewer."""
        changed = self._sessionManager.setStage(stage)
        if changed:
            self.refresh()

    def addPrimPaths(self, primPaths, replace=False):
        """Add a given list of prim paths to the viewer.

        Args:
            primPaths (list[str]): List of prim paths to get from the stage and add to the view.
            replace (bool): If True, will clear the current uv's from the view before adding anything new.
        """
        extractors = self._sessionManager.addPrimPaths(primPaths, replace)
        if extractors or replace:
            self._updateUvSetNameOptions()
            self._updateTextureOptions()
            self.updateUVs(extractors=extractors, replace=replace)

    def addPrims(self, prims, replace=False):
        """Add a list of usd prims to the viewer.

        Args:
            prims (Usd.Prim): List of prims to get from the stage and add to the view.
            replace (bool): If True, will clear the current uv's from the view before adding anything new.
        """
        extractors = self._sessionManager.addPrims(prims, replace)
        if extractors or replace:
            self._updateUvSetNameOptions()
            self._updateTextureOptions()
            self.updateUVs(extractors=extractors, replace=replace)

    def updateUVs(self, uvSetName=None, extractors=None, replace=False):
        """Update the view with new shape data.

        Args:
            uvSetName (str | None):
                The uv set name to use. If None, get the active uv set name from the session manager.
            extractors (list[uc_usdextractor.PrimDataExtractor] | None):
                A list of extractors to pull the shape data from. If None, get the list of
                cached extractors from the session manager.
            replace (bool): If True, will clear the current uv's from the view before adding anything new.
        """
        if replace:
            self._view.clear()
        shapeData = self._sessionManager.getShapeData(uvSetName, extractors)
        if self._displayUVBorder:
            shapeData.extend(
                self._sessionManager.getShapeEdgeBorderData(uvSetName, extractors)
            )
        if shapeData:
            self._view.addShapes(shapeData)

    def displayUVBorders(self, display):
        """Set the display of uv border edges in the viewer."""
        display = bool(display)
        if display == self._displayUVBorder:
            return

        if display:
            shapeData = self._sessionManager.getShapeEdgeBorderData()
            if shapeData:
                self._view.addShapes(shapeData)
        else:
            shapesToRemove = []
            for shape in self._view.shapes():
                identifier = shape.identifier()
                if identifier.endswith(
                    self._sessionManager.EDGE_BORDER_IDENTIFIER_SUFFIX
                ):
                    shapesToRemove.append(identifier)
            if shapesToRemove:
                self._view.removeShapes(shapesToRemove)
        self._displayUVBorder = display

    def updateTexture(self, path=None):
        """Update the texture used in the view.

        Args:
            path (str | None):
                The texture path to use. If None, get the active texture path from the session manager.
        """
        pathToSet = path if path else self._sessionManager.activeTexturePath()
        if not pathToSet:
            logger.debug("No texture path to set.")
            return
        self._view.setTexturePath(pathToSet)

    def refresh(self):
        """Refresh the viewer with the current cache extractors and uvName."""
        self._view.clear()
        self._sessionManager.refresh()
        self._updateUvSetNameOptions()
        self._updateTextureOptions()
        self.updateUVs()

    def clear(self):
        """Clear the viewer of any uvs currently drawn on the screen."""
        self._sessionManager.clear()
        self._view.clear()


class UViewSDWindow(QtWidgets.QMainWindow, UViewSDMixin):
    def __init__(self, stage=None, config=None, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent=parent)
        UViewSDMixin.__init__(self, stage=stage, config=config)
        widget = QtWidgets.QWidget()
        widget.setLayout(self._layout)
        self.setCentralWidget(widget)
        self.setWindowTitle("UViewSD")


class UViewSDWidget(QtWidgets.QWidget, UViewSDMixin):
    def __init__(self, stage=None, config=None, parent=None):
        QtWidgets.QWidget.__init__(self, parent=parent)
        UViewSDMixin.__init__(self, stage=stage, config=config)
        self.setLayout(self._layout)
