from PySide2 import QtWidgets, QtCore
import numpy as np


def stateFromEvent(event):
    modifiers = QtWidgets.QApplication.keyboardModifiers()
    button = event.button()
    for state in [PanState, ZoomState]:
        if state.canEnable(modifiers, button):
            return state
    return None


class BaseState:
    def __init__(self, event, camera, width, height):
        self._camera = camera
        self._initProjMat = self._camera._projMat
        self._width = width
        self._height = height
        [self._initX, self._initY] = self.glScreenCoord(event)

    def glScreenCoord(self, event):
        position = event.pos()
        screenCoords = [position.x() / self._width, position.y() / self._height]
        return self._camera.mapScreenToGl(screenCoords)

    def worldCoord(self, event):
        position = event.pos()
        screenCoords = [position.x() / self._width, position.y() / self._height]
        return self._camera.mapScreenToWorld(screenCoords)

    @staticmethod
    def canEnable(modifiers, button):
        return False

    @staticmethod
    def shouldDisable(button):
        return True

    def update(self, event):
        return False


class ZoomState(BaseState):
    def __init__(self, event, camera, width, height):
        BaseState.__init__(self, event, camera, width, height)
        [self._initX, self._initY] = self.worldCoord(event)

    @staticmethod
    def canEnable(modifiers, button):
        return modifiers == QtCore.Qt.AltModifier and button == QtCore.Qt.RightButton

    @staticmethod
    def shouldDisable(button):
        return button == QtCore.Qt.RightButton

    def update(self, event):
        [xPos, yPos] = self.worldCoord(event)
        xZoom = xPos - self._initX
        yZoom = self._initY - yPos
        zoomAmount = 1 + (xZoom + yZoom) / 2
        zoomedProjectionMatrix = self._camera.scaleMatrixAroundPoint(self._initProjMat, zoomAmount, [self._initX, self._initY])
        self._camera.setProjectionMatrix(zoomedProjectionMatrix)
        return True


class PanState(BaseState):
    def __init__(self, event, camera, width, height):
        BaseState.__init__(self, event, camera, width, height)
        self._scale = self._initProjMat[0][0]

    @staticmethod
    def canEnable(modifiers, button):
        return modifiers == QtCore.Qt.AltModifier and button == QtCore.Qt.MiddleButton

    @staticmethod
    def shouldDisable(button):
        return button == QtCore.Qt.MiddleButton

    def update(self, event):
        [x, y] = self.glScreenCoord(event)
        transformMatrix = self._camera.createTransformationMatrix(
            (x - self._initX) / self._scale,
            (y - self._initY) / self._scale
        )
        self._camera.setProjectionMatrix(np.matmul(self._initProjMat, transformMatrix))
        return True
