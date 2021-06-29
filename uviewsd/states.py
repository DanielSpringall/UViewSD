# Copyright 2021 by Daniel Springall.
# This file is part of UViewSD, and is released under the "MIT License Agreement".
# Please see the LICENSE file that should have been included as part of this package.
from PySide2 import QtWidgets, QtCore
import numpy as np


class BaseState:
    # Button trigger to enable/disable the state. Required.
    EVENT_BUTTON = None
    # Key modifiers held during trigger to enable/disable the state. Not required.
    EVENT_MODIFIERS = None

    def __init__(self, event, camera, width, height):
        self._camera = camera

        self._initProjMat = self._camera.projectionMatrix()
        self._initGlScreenCoord = self._glScreenCoord(event)
        self._initXScale = self._initProjMat[0][0]
        self._initYScale = self._initProjMat[1][1]

    def _glScreenCoord(self, event):
        """Get the GL screen co-ordinates from a Qt event.

        Args:
            event (QtCore.QEvent): The event to get the co-ordinates from.
        Return:
            list[float, float]: The GL screen co-ordinates.
        """
        position = event.pos()
        return self._camera.mapScreenToGl([position.x(), position.y()])

    @classmethod
    def canEnable(cls, modifiers, button):
        """Test if this event should be enabled based on a class defined list of pressed button and modifiers.

        Args:
            modifiers (Qt.KeyboardModifiers): The list of keyboard modifiers to test.
            button (Qt.MouseButton): The buttont to test.
        Return
            bool: True if modifiers/button match the enable state requirements. False otherwise.
        """
        if cls.EVENT_BUTTON is None:
            raise RuntimeError(
                "No button specified to test if {} can be enabled.".format(cls.__name__)
            )
        if button != cls.EVENT_BUTTON:
            return False
        if cls.EVENT_MODIFIERS is not None and cls.EVENT_MODIFIERS != modifiers:
            return False
        return True

    @classmethod
    def shouldDisable(cls, button):
        """Test if this event should be disabled based on a class defined button.

        Args:
            button (Qt.MouseButton): The buttont to test.
        Return
            bool: True if button matches the disable state requirements. False otherwise.
        """
        # Note: We want the UX behaviour of being able to start the event with modifiers + button,
        # but then release the modifier whilst moving the mouse. So we only need to do a button
        # comparison here.
        if cls.EVENT_BUTTON is None:
            raise RuntimeError(
                "No button specified to test if {} should be disabled.".format(
                    cls.__name__
                )
            )
        return button == cls.EVENT_BUTTON

    def update(self, event):
        """Trigger and update of the state.

        Args:
            event (QtCore.QEvent): The event to update from.
        Return:
            bool: True if an update occured. False otherwise.
        """
        return False


class ZoomState(BaseState):
    """Mouse drag zoom in/out."""

    EVENT_BUTTON = QtCore.Qt.RightButton
    EVENT_MODIFIERS = QtCore.Qt.AltModifier

    def __init__(self, event, camera, width, height):
        BaseState.__init__(self, event, camera, width, height)
        self._initWorldCoord = self._camera.mapGlToWorld(self._initGlScreenCoord)

    def update(self, event):
        screenCoord = self._glScreenCoord(event)
        xZoom = screenCoord[0] - self._initGlScreenCoord[0]
        yZoom = self._initGlScreenCoord[1] - screenCoord[1]
        zoomAmount = max(0.01, 1 + (xZoom + yZoom) / 2.0)
        zoomedProjectionMatrix = self._camera.scaleMatrixAroundPoint(
            matrix=self._initProjMat,
            xScale=zoomAmount,
            yScale=zoomAmount,
            coord=self._initWorldCoord,
        )
        self._camera.setProjectionMatrix(zoomedProjectionMatrix)
        return True


class PanState(BaseState):
    """Mouse drag pan state."""

    EVENT_BUTTON = QtCore.Qt.MiddleButton
    EVENT_MODIFIERS = QtCore.Qt.AltModifier

    def update(self, event):
        screenCoord = self._glScreenCoord(event)
        transformMatrix = self._camera.createTransformationMatrix(
            (screenCoord[0] - self._initGlScreenCoord[0]) / self._initXScale,
            (screenCoord[1] - self._initGlScreenCoord[1]) / self._initYScale,
        )
        self._camera.setProjectionMatrix(np.matmul(self._initProjMat, transformMatrix))
        return True


AVAILABLE_STATES = [PanState, ZoomState]


def stateFromEvent(event):
    """Test for a valid state from a given event and it's triggers.

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
