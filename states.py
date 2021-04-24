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
        [self._initXPos, self._initYPos] = self.glScreenPosition(event)

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
        self._initProjMat = np.matrix.transpose(self._initProjMat)

    @staticmethod
    def canEnable(modifiers, button):
        return modifiers == QtCore.Qt.AltModifier and button == QtCore.Qt.RightButton

    @staticmethod
    def shouldDisable(button):
        return button == QtCore.Qt.RightButton

    def update(self, event):
        [xPos, yPos] = self.glScreenPosition(event)
        xZoom = xPos - self._initXPos
        yZoom = self._initYPos - yPos
        zoomAmount = 1 + (xZoom + yZoom) / 2

        zoomedProjectionMatrix = np.matrix.transpose(
            self._camera.scaleMatrix(self._initProjMat, zoomAmount, self._transMat, self._invTransMat)
        )

        self._camera.setProjectionMatrix(zoomedProjectionMatrix)
        return True


class PanState(BaseState):
    def __init__(self, event, camera, width, height):
        BaseState.__init__(self, event, camera, width, height)

    @staticmethod
    def canEnable(modifiers, button):
        return modifiers == QtCore.Qt.AltModifier and button == QtCore.Qt.LeftButton

    @staticmethod
    def shouldDisable(button):
        return button == QtCore.Qt.LeftButton

    def update(self, event):
        [xPos, yPos] = self.glScreenPosition(event)

        transformMatrix = self._camera.createTransformationMatrix(
            xPos - self._initXPos,
            yPos - self._initYPos
        )
        projMat = np.matmul(self._initProjMat, transformMatrix)
        self._camera.setProjectionMatrix(projMat)
        return True
