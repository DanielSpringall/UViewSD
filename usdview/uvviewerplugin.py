import window

from pxr import Tf
from pxr.Usdviewq.plugin import PluginContainer


class UVViewerPluginContainer(PluginContainer):
    def registerPlugins(self, plugRegistry, usdviewApi):
        self._windowModule = self.deferredImport("window")
        self._openWindow = plugRegistry.registerCommandPlugin(
            "UVViewerPluginContainer.openWindow",
            "Viewer",
            self.launchWindow)

    def configureView(self, plugRegistry, plugUIBuilder):
        uvMenu = plugUIBuilder.findOrCreateMenu("UV")
        uvMenu.addItem(self._openWindow)

    def launchWindow(self, usdviewApi):
        window = USDViewerUVWindow(usdviewApi=usdviewApi)
        window.show()


class USDViewerUVWindow(window.UVViewerWindow):
    def __init__(self, usdviewApi):
        window.UVViewerWindow.__init__(
            self,
            stage=usdviewApi.stage,
            parent=usdviewApi.qMainWindow,
        )
        self._usdviewApi = usdviewApi

    def _setupConnections(self):
        window.UVViewerWindow._setupConnections(self)
        self._usdviewApi.dataModel.selection.signalPrimSelectionChanged.connect(self.selectionChanged)

    def selectionChanged(self, *args, **kwargs):
        selectedPaths = self._usdviewApi.selectedPaths
        if selectedPaths:
            self.addPrimPaths(selectedPaths, override=True)
        else:
            self._view.clear()

    def stageChanged(self, *args, **kwargs):
        self.setStage(self._usdviewApi.stage)


Tf.Type.Define(UVViewerPluginContainer)
