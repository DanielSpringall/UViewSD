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
        self._windowModule.run(usdviewApi)


Tf.Type.Define(UVViewerPluginContainer)
