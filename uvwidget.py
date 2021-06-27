# Copyright 2021 by Daniel Springall.
# This file is part of UViewSD, and is released under the "MIT License Agreement".
# Please see the LICENSE file that should have been included as part of this package.
from PySide2 import QtWidgets, QtGui, QtCore
from OpenGL import GL

import shape
import states
import camera
import logging

logger = logging.getLogger(__name__)


class UVViewerWidget(QtWidgets.QOpenGLWidget):
    def __init__(self, *args, **kwargs):
        QtWidgets.QOpenGLWidget.__init__(self, *args, **kwargs)

        self._painter = None
        self._uvInfoFont = None
        self._gridNumbersFont = None

        self._activeState = None
        self._backgroundGrid = None
        self._shapes = []
        self._camera = None

        self._showGrid = True
        self._showCurrentMouseUVPosition = True

        self.setMouseTracking(self._showCurrentMouseUVPosition)
        self.setMinimumSize(400, 400)

    # SHAPE MANAGEMENT
    def addShapes(self, shapes):
        """ Add a list of shapes to be drawn in the scene and refresh the view.
        Existing shapes with the same name will be overridden.

        Args:
            shapes (list[shape.UVShape]): List of shapes to draw.
        """
        shapeNamesToAdd = [shape.identifier for shape in shapes]
        currentShapeNames = [shape.identifier for shape in self._shapes]
        shapesToRemove = list(set(shapeNamesToAdd).intersection(set(currentShapeNames)))
        if shapesToRemove:
            self.removeShapes(shapesToRemove, update=False)
        self._shapes.extend(shapes)
        self.update()

    def removeShapes(self, shapeNames, update=True):
        """ CLear a list of shapes from the view
        
        Args:
            shapeNames (list[str]): Names of the shapes to remove from the view.
            update (bool): If true, trigger a UI update if any shapes have been removed.
        """
        if not self._shapes:
            return

        shapesRemoved = False
        for shapeName in shapeNames:
            shapeToRemove = None
            for _shape in self._shapes:
                if _shape.identifier() == shapeName:
                    shapeToRemove = _shape
                    break
            if shapeToRemove is None:
                continue
            self._shapes.remove(shapeToRemove)
            del shapeToRemove
            shapesRemoved = True

        if shapesRemoved and update:
            self.update()

    def clear(self):
        """ Clear all the current shapes drawn in the view. """
        if not self._shapes:
            return
        self._shapes = []
        self.update()

    # VIEW ACTIONS
    def toggleGridVisibility(self):
        """ Toggle the visible state of the grid lines and numbers in the view. """
        self._showGrid = not self._showGrid
        self.update()

    def toggleMouseUVPositionDisplay(self):
        """ Toggle the display of the uv position at the current mouse position in the bottom left of the widget. """
        self._showCurrentMouseUVPosition = not self._showCurrentMouseUVPosition
        self.setMouseTracking(self._showCurrentMouseUVPosition)
        self.update()

    def focusOnBBox(self):
        """ Focus the viewer on the bbox surounding all the currently displayed shapes. """
        if not self._shapes:
            self._camera.focus(0, 1, 1, 0)
        else:
            bbox = None
            for _shape in self._shapes:
                if bbox is None:
                    bbox = _shape.bbox()
                else:
                    bbox.updateWithBBox(_shape.bbox())
            self._camera.focus(bbox.xMin, bbox.xMax, bbox.yMax, bbox.yMin)
        self.update()

    # QT EVENTS
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_F:
            self.focusOnBBox()
            event.accept()
        QtWidgets.QOpenGLWidget.keyPressEvent(self, event)

    def mousePressEvent(self, event):
        """ Override to add custom state handling. """
        if not self._activeState:
            state = states.stateFromEvent(event)
            if state:
                self._activeState = state(event, self._camera, self.width(), self.height())
                event.accept()
        QtWidgets.QOpenGLWidget.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):
        """ Override to add custom state handling. """
        if (
            (self._activeState and self._activeState.update(event)) or
            self._showCurrentMouseUVPosition
        ):
            self.update()
            event.accept()
        QtWidgets.QOpenGLWidget.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event):
        """ Override to add custom state handling. """
        if self._activeState and self._activeState.shouldDisable(event.button()):
            self._activeState = None
            event.accept()
        QtWidgets.QOpenGLWidget.mouseReleaseEvent(self, event)

    def wheelEvent(self, event):
        """ Override to add custom GL zoom. """
        QtWidgets.QOpenGLWidget.wheelEvent(self, event)

        # Perform graph zoom on mouse cursor position
        if not self._activeState:
            pos = event.pos()
            glCoords = self._camera.mapScreenToGl([pos.x(), pos.y()])
            worldCoords = self._camera.mapGlToWorld(glCoords)
            delta = event.angleDelta().y()
            zoomAmount = 1 + (delta and delta // abs(delta)) * 0.03
            self._camera.zoom(worldCoords, zoomAmount)
            self.update()

    # GL EVENTS
    def initializeGL(self):
        """ Setup GL objects for the view ready for drawing. """
        self._backgroundGrid = shape.Grid()
        self._camera = camera.Camera2D(self.width(), self.height())
        self._painter = QtGui.QPainter()

        self._gridNumbersFont = QtGui.QFont()
        self._gridNumbersFont.setPointSize(8)
        self._uvInfoFont = QtGui.QFont()
        self._uvInfoFont.setPointSize(12)

    def resizeGL(self, width, height):
        """ Resize the GL viewport and update the camera with the new dimensions. """
        GL.glViewport(0, 0, width, height)
        self._camera.resize(width, height)

    def paintGL(self):
        """ Paint all the GL objects in the scene. """
        self._painter.begin(self)

        self._painter.beginNativePainting()
        GL.glClearColor(0.3, 0.3, 0.3, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        projectionMatrix = self._camera.glProjectionMatrix()
        if self._showGrid:
            self._backgroundGrid.draw(projectionMatrix)
        for _shape in self._shapes:
            _shape.draw(projectionMatrix)
        self._painter.endNativePainting()

        if self._showGrid:
            self._drawText(self._painter)
        if self._drawMouseUVPosition:
            self._drawMouseUVPosition(self._painter)
        self._painter.end()

    def _drawText(self, painter):
        """ Paint the grid values in the scene. """
        originCoord = self._camera.mapWorldToScreen([0.0, 0.0])
        offsetCoord = self._camera.mapWorldToScreen([0.1, 0.1])

        width = offsetCoord[0] - originCoord[0]
        height = originCoord[1] - offsetCoord[1]
        doubleWidth = width * 2
        # Offset x a little to prevent intersection with the vertical grid line
        originX = originCoord[0] + width / 20
        originY = originCoord[1] - height

        def drawText(increment, xAxis=True):
            offset = float(increment) / 10
            if xAxis:
                left = originX + increment * width
                top = originY
            else:
                left = originX
                top = originY - increment * height

            text = str(offset)
            painter.drawText(left, top, doubleWidth, height, QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom, text)

        painter.setPen(QtCore.Qt.black)
        painter.setFont(self._gridNumbersFont)
        drawText(0)
        # Draw the rest of the text
        for i in range(1, self._backgroundGrid.TOTAL_LINES + 1):
            drawText(i, xAxis=True)
            drawText(-i, xAxis=True)
            drawText(i, xAxis=False)
            drawText(-i, xAxis=False)

    def _drawMouseUVPosition(self, painter):
        """ Draw the corresponding uv position from the current mouse position over the widget. """
        cursor = QtGui.QCursor()
        position = self.mapFromGlobal(cursor.pos())
        uvPos = self._camera.mapScreenToWorld([position.x(), position.y()])
        displayString = "UV: %.3f, %.3f" % (uvPos[0], uvPos[1])

        painter.setPen(QtCore.Qt.white)
        painter.setFont(self._uvInfoFont)
        painter.drawText(5, self.height() - 40, 200, 40, QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom, displayString)
