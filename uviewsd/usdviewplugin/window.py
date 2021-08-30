# Copyright 2021 by Daniel Springall.
# This file is part of UViewSD, and is released under the "MIT License Agreement".
# Please see the LICENSE file that should have been included as part of this package.
from uviewsd.widget import UViewSDWindow


class USDViewerUVWindow(UViewSDWindow):
    def __init__(self, usdviewApi):
        UViewSDWindow.__init__(self, parent=usdviewApi.qMainWindow)
        self._usdviewApi = usdviewApi
        self.setStage(self._usdviewApi.stage)
        usdviewApi.dataModel.selection.signalPrimSelectionChanged.connect(
            self.selectionChanged
        )

        # Trigger the selection update call in case the user had something selected
        # before the window was opened.
        self.selectionChanged()
        self.show()

    def selectionChanged(self, *args, **kwargs):
        selectedPaths = self._usdviewApi.selectedPaths
        if selectedPaths:
            self.addPrimPaths(selectedPaths, replace=True)
        else:
            self.clear()
