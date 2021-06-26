from PySide2 import QtWidgets, QtCore
import numpy as np


def stateFromEvent(event):
    """ Test for a valid state from a given event and it's triggers. 

    Args:
        event (QtCore.QEvent): The event to test from.
    Return:
        (State or None): The state class that matches the event triggers, or None if no match can be found.
    """
    modifiers = QtWidgets.QApplication.keyboardModifiers()
    button = event.button()
    for state in AVAILABLE_STATES:
        if state.canEnable(modifiers, button):
            return state
    return None


class BaseState:
    def __init__(self, event, camera, width, height):
        self._camera = camera

        self._initProjMat = self._camera.projectionMatrix()
        self._initGlScreenCoord = self._glScreenCoord(event)
        self._initWorldCoord = self._camera.mapGlToWorld(self._initGlScreenCoord)
        self._initXScale = self._initProjMat[0][0]
        self._initYScale = self._initProjMat[1][1]

    def _glScreenCoord(self, event):
        """ Get the GL screen co-ordinates from a Qt event.

        Args:
            event (QtCore.QEvent): The event to get the co-ordinates from.
        Return:
            list[float, float]: The GL screen co-ordinates.
        """
        position = event.pos()
        return self._camera.mapScreenToGl([position.x(), position.y()])

    @staticmethod
    def canEnable(modifiers, button):
        """ Test if this event should be enabled based on a given set of modifiers and buttons.

        Args:
            modifiers (Qt.KeyboardModifiers): The list of keyboard modifiers to test.
            button (Qt.MouseButton): The buttont to test.
        Return
            bool: True if modifiers/button match the enable state requiorements. False otherwise.
        """
        return False

    @staticmethod
    def shouldDisable(button):
        """ Test if this event should be disabled based on a given set of modifiers and buttons.

        Args:
            modifiers (Qt.KeyboardModifiers): The list of keyboard modifiers to test.
            button (Qt.MouseButton): The buttont to test.
        Return
            bool: True if modifiers/button match the disable state requiorements. False otherwise.
        """
        return True

    def update(self, event):
        """ Trigger and update of the state.

        Args:
            event (QtCore.QEvent): The event to update from.
        Return:
            bool: True if an update occured. False otherwise.
        """
        return False


class ZoomState(BaseState):
    """ Mouse drag zoom in/out. """

    @staticmethod
    def canEnable(modifiers, button):
        return modifiers == QtCore.Qt.AltModifier and button == QtCore.Qt.RightButton

    @staticmethod
    def shouldDisable(button):
        return button == QtCore.Qt.RightButton

    def update(self, event):
        screenCoord = self._glScreenCoord(event)
        xZoom = screenCoord[0] - self._initGlScreenCoord[0]
        yZoom = self._initGlScreenCoord[1] - screenCoord[1]
        zoomAmount = max(0.01, 1 + (xZoom + yZoom) / 2.0)
        zoomedProjectionMatrix = self._camera.scaleMatrixAroundPoint(
            matrix=self._initProjMat,
            xScale=zoomAmount,
            yScale=zoomAmount,
            coord=self._initWorldCoord
        )
        self._camera.setProjectionMatrix(zoomedProjectionMatrix)
        return True


class PanState(BaseState):
    """ Mouse drag pan state. """

    @staticmethod
    def canEnable(modifiers, button):
        return modifiers == QtCore.Qt.AltModifier and button == QtCore.Qt.LeftButton

    @staticmethod
    def shouldDisable(button):
        return button == QtCore.Qt.LeftButton

    def update(self, event):
        screenCoord = self._glScreenCoord(event)
        transformMatrix = self._camera.createTransformationMatrix(
            (screenCoord[0] - self._initGlScreenCoord[0]) / self._initXScale,
            (screenCoord[1] - self._initGlScreenCoord[1]) / self._initYScale,
        )
        self._camera.setProjectionMatrix(np.matmul(self._initProjMat, transformMatrix))
        return True


class ResizeState:
    """ Custom state to handle the resize event of the UI. """

    def __init__(self):
        pass


AVAILABLE_STATES = [PanState, ZoomState]
