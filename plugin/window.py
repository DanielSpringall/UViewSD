import window


class USDViewerUVWindow(window.UVViewerWindow):
    def __init__(self, usdviewApi):
        self._usdviewApi = usdviewApi
        window.UVViewerWindow.__init__(
            self,
            stage=usdviewApi.stage,
            parent=usdviewApi.qMainWindow,
        )

    def _setupConnections(self):
        window.UVViewerWindow._setupConnections(self)
        self._usdviewApi.dataModel.selection.signalPrimSelectionChanged.connect(self.selectionChanged)

    def selectionChanged(self, *args, **kwargs):
        selectedPaths = self._usdviewApi.selectedPaths
        if selectedPaths:
            self.addPrimPaths(selectedPaths, replace=True)
        else:
            self._view.clear()
