# Copyright 2021 by Daniel Springall.
# This file is part of UViewSD, and is released under the "MIT License Agreement".
# Please see the LICENSE file that should have been included as part of this package.
from uviewsd import window


class USDViewerUVWindow(window.UVViewerWindow):
    def __init__(self, usdviewApi):
        self._usdviewApi = usdviewApi
        window.UVViewerWindow.__init__(
            self,
            stage=usdviewApi.stage,
            parent=usdviewApi.qMainWindow,
        )
        # Trigger the selection update call in case the user had something selected
        # before the window was opened.
        self.selectionChanged()

    def _setupConnections(self):
        window.UVViewerWindow._setupConnections(self)
        self._usdviewApi.dataModel.selection.signalPrimSelectionChanged.connect(
            self.selectionChanged
        )

    def selectionChanged(self, *args, **kwargs):
        selectedPaths = self._usdviewApi.selectedPaths
        if selectedPaths:
            self.addPrimPaths(selectedPaths, replace=True)
        else:
            self._view.clear()
