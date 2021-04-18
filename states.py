from PySide2.QtWidgets import QApplication
from PySide2.QtCore import Qt
import numpy as np


def stateFromEvent(event):
    modifiers = QApplication.keyboardModifiers()
    button = event.button()
    for state in [PanState, ZoomState]:
        if state.canEnable(modifiers, button):
            return state
    return None


class BaseState:
    def __init__(self, event, camera, width, height):
        self._camera = camera
        self._initialProjectionMatrix = self._camera._projectionMatrix
        self._width = width
        self._height = height
        [self._initialXPos, self._initialYPos] = self.glScreenPosition(event)

    def glScreenPosition(self, event):
        position = event.pos()
        screenCoords = [position.x() / self._width, position.y() / self._height]
        return self._camera.screenToGlCoord(screenCoords)

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
        pos = event.pos()
        worldCoords = self._camera.screenToWorldCoord([pos.x()/width, pos.y()/height])
        self._transMat = np.matrix.transpose(self._camera.createTransformationMatrix(-worldCoords[0], -worldCoords[1]))
        self._invTransMat = np.matrix.transpose(self._camera.createTransformationMatrix(worldCoords[0], worldCoords[1]))
        self._initialProjectionMatrix = np.matrix.transpose(self._initialProjectionMatrix)

    @staticmethod
    def canEnable(modifiers, button):
        return modifiers == Qt.AltModifier and button == Qt.RightButton

    @staticmethod
    def shouldDisable(button):
        return button == Qt.RightButton

    def update(self, event):
        [xPos, yPos] = self.glScreenPosition(event)
        xZoom = xPos - self._initialXPos
        yZoom = self._initialYPos - yPos
        zoomAmount = 1 + (xZoom + yZoom) / 2

        zoomedProjectionMatrix = np.matrix.transpose(
            self._camera.scaleMatrix(self._initialProjectionMatrix, zoomAmount, self._transMat, self._invTransMat)
        )

        self._camera.setProjectionMatrix(zoomedProjectionMatrix)
        return True


class PanState(BaseState):
    def __init__(self, event, camera, width, height):
        BaseState.__init__(self, event, camera, width, height)

    @staticmethod
    def canEnable(modifiers, button):
        return modifiers == Qt.AltModifier and button == Qt.MiddleButton

    @staticmethod
    def shouldDisable(button):
        return button == Qt.MiddleButton

    def update(self, event):
        [xPos, yPos] = self.glScreenPosition(event)

        transformMatrix = self._camera.createTransformationMatrix(
            xPos - self._initialXPos,
            yPos - self._initialYPos
        )
        projMat = np.matmul(self._initialProjectionMatrix, transformMatrix)
        self._camera.setProjectionMatrix(projMat)
        return True
