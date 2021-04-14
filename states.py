from PySide2.QtWidgets import QApplication
from PySide2.QtCore import Qt
import numpy as np


def getState(event):
    modifiers = QApplication.keyboardModifiers()
    button = event.button()
    for state in [PanState, ZoomState]:
        if state.canEnable(modifiers, button):
            return state
    return None


class BaseState:
    def __init__(self, event, camera):
        self._initialPos = self.positionFromEvent(event)
        self._camera = camera

    @staticmethod
    def positionFromEvent(event):
        position = event.pos()
        return np.array((position.x(), position.y()))

    @staticmethod
    def canEnable(modifiers, button):
        return False

    @staticmethod
    def shouldDisable(button):
        return True

    def update(self, event):
        return False


class ZoomState(BaseState):
    def __init__(self, event, camera):
        BaseState.__init__(self, event, camera)
        self._initialZoom = self._camera._zoom

    @staticmethod
    def canEnable(modifiers, button):
        return modifiers == Qt.AltModifier and button == Qt.RightButton

    @staticmethod
    def shouldDisable(button):
        return button == Qt.RightButton

    def update(self, event):
        currentPosition = self.positionFromEvent(event)
        xZoom = (currentPosition[0] - self._initialPos[0]) / self._camera._width
        yZoom = (currentPosition[1] - self._initialPos[1]) / self._camera._height
        averagedZoom = (xZoom + yZoom) / 2
        zoomAmount = self._initialZoom + averagedZoom
        self._camera.zoom(self._initialPos, zoomAmount)
        return True


class PanState(BaseState):
    def __init__(self, event, camera):
        BaseState.__init__(self, event, camera)

    @staticmethod
    def canEnable(modifiers, button):
        return modifiers == Qt.AltModifier and button == Qt.MiddleButton

    @staticmethod
    def shouldDisable(button):
        return button == Qt.MiddleButton

    def update(self, event):
        currentPosition = self.positionFromEvent(event)
        xTransform = (currentPosition[0] - self._initialPos[0]) * 2
        yTransform = (self._initialPos[1] - currentPosition[1]) * 2
        self._camera.pan(np.array((xTransform, yTransform), dtype=np.float32))
        self._initialPos = currentPosition
        return True
