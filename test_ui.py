from uviewsd import uviewsdwidget

from PySide2 import QtWidgets, QtCore

import logging
from pxr import Usd


logger = logging.getLogger(__name__)


def run():
    logger.setLevel(logging.DEBUG)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseDesktopOpenGL)
    app = QtWidgets.QApplication([])

    stage = None
    primPaths = []

    # ATTIC
    stage = Usd.Stage.Open(
        "C:\\Libraries\\USD\\share\\usd\\Attic_NVIDIA\\Attic_NVIDIA.usd"
    )
    primPaths = ["/Root/Geometry/clock_475/clock/Section1"]

    # KITCHEN
    # stage = Usd.Stage.Open(
    #     "C:\\Libraries\\USD\\share\\usd\\kitchenSet\\Kitchen_set.usd"
    # )
    # primPaths = [
    #     "/Kitchen_set/Props_grp/West_grp/WestWall_grp/FramePictureOval_1/Geom/FramePictureOval"
    # ]

    # TESTS
    # stage = Usd.Stage.Open("C:\\Users\\Daniel\\Projects\\Python\\UViewSD\\uviewsd\\tests\\data\\uvborders.usda")
    # primPaths = ['/cube']

    _window = uviewsdwidget.UViewSDWidget(stage)
    _window.addPrimPaths(primPaths)
    _window.show()

    app.exec_()


if __name__ == "__main__":
    run()
