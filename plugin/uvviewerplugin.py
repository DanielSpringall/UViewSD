from pxr import Tf
from pxr.Usdviewq.plugin import PluginContainer


class UVViewerPluginContainer(PluginContainer):
    def registerPlugins(self, plugRegistry, usdviewApi):
        self._windowModule = self.deferredImport("plugin.window")
        self._openWindow = plugRegistry.registerCommandPlugin(
            "UVViewerPluginContainer.launchWindow",
            "Viewer",
            self.launchWindow)

    def configureView(self, plugRegistry, plugUIBuilder):
        uvMenu = plugUIBuilder.findOrCreateMenu("UV")
        uvMenu.addItem(self._openWindow)

    def launchWindow(self, usdviewApi):
        window = self._windowModule.USDViewerUVWindow(usdviewApi=usdviewApi)
        window.show()


Tf.Type.Define(UVViewerPluginContainer)
