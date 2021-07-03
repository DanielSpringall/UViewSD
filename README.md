# UViewSD

UViewSD is a python UV viewer for USD data. It comes setup as a usdview plugin, but can easily be extended to be used inside DCC applications.

Note: UViewSD is NOT an editor, there is no way to edit and save out uv tweaks within the UI.

![UViewSD UI](./resources/uviewsd_ui.png)

## Configuration
![UViewSD Configuration](./resources/uviewsd_configuration.png)

1. UV Set name.
    - This option box will be made up of the avaiable uv names in the current mesh selection.
        - See [PrimDataExtractor](./uviewsd/shape.py) for more information on how these names are discovered.
    - Changing the active uv set will change it for all selected meshes in the view. So if a shape doesn't contain the specific uv set selected, nothing will be displayed for that shape.
2. UV Borders.
    - Toggle the thick line on/off for the UV edge borders.
3. Grid.
    - Toggle the background grid and numbers on/off.
4. UV Position.
    - Toggle the display in the bottom left of the view of the UV value corresponding to the current mouse position in the view.

## View Navigation
- Pan
    - Alt + Middle Mouse Button.
- Zoom
    - Scroll wheel.
    - Alt + Right Mouse Button.
- Focus
    - F.

## Usdview Plugin
Setting up UViewSD for use in usdview is straight forward. Add the `/local/path/to/UViewSD` to your `PYTHONPATH` environment variable. Then add or append `/local/path/to/UViewSD/uviewsd/plugin` to the `PXR_PLUGINPATH_NAME` environment variable. The next time you launch usdview you will be able to launch the UViewSD window from the menu. UV->Viewer.

![Usdview Menu](./resources/usdview_menu.png)

Any meshes selected in usdview should be synced to the UViewSD widget.

## DCC Applications
There is no setup currently for DCC applications, to create one yourself take a look at [USDView Window](https://github.com/DanielSpringall/UViewSD/blob/main/uviewsd/plugin/window.py) for more information. For a minimum setup you will need to work out how to pass the usd stage to the window class, and how to pass the prim paths of the prims in the stage you want to view.

## Dependencies
- [USD](https://github.com/PixarAnimationStudios/USD)
- [PySide2](http://wiki.qt.io/PySide2)
- [PyOpenGL](https://pypi.python.org/pypi/PyOpenGL/)
- [numpy](https://numpy.org/)
