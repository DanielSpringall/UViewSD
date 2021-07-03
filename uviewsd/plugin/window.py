# Copyright 2021 by Daniel Springall.
# This file is part of UViewSD, and is released under the "MIT License Agreement".
# Please see the LICENSE file that should have been included as part of this package.
from uviewsd import uviewsdwidget
from PySide2 import QtWidgets


class USDViewerUVWindow(QtWidgets.QMainWindow):
    def __init__(self, usdviewApi):
        self._usdviewApi = usdviewApi

        parent = usdviewApi.qMainWindow
        QtWidgets.QMainWindow.__init__(self, parent=parent)

        stage = usdviewApi.stage
        self._uvWidget = uviewsdwidget.UViewSDWidget(stage=stage, parent=self)
        self.setWindowTitle(self._uvWidget.windowTitle())
        self.setCentralWidget(self._uvWidget)

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
            self._uvWidget.addPrimPaths(selectedPaths, replace=True)
        else:
            self._uvWidget.clear()
