# Copyright 2021 by Daniel Springall.
# This file is part of UViewSD, and is released under the "MIT License Agreement".
# Please see the LICENSE file that should have been included as part of this package.
from uviewsd import shape
from uviewsd import states
from uviewsd import camera
from uviewsd import shader

from PySide2 import QtWidgets, QtGui, QtCore
from OpenGL import GL

import logging

logger = logging.getLogger(__name__)


class UVViewerWidget(QtWidgets.QOpenGLWidget):
    """Widget responsible for drawing the GL elements."""

    def __init__(self, config=None, parent=None):
        QtWidgets.QOpenGLWidget.__init__(self, parent=parent)

        self._painter = None
        self._uvInfoFont = None
        self._gridNumbersFont = None
        self._backgroundColor = (0.3, 0.3, 0.3, 1.0)

        self._activeState = None
        self._backgroundGrid = None
        self._textureShape = None
        self._shapes = []
        self._camera = None
        self._shader = None

        config = config if config is not None else ViewerConfiguration()
        self._showTexture = config.displayTexture
        self._showGrid = config.displayGrid
        self._showUVEdgeBoundaryHighlight = config.displayUVBorder
        self._showCurrentMouseUVPosition = config.displayUVPos

        self.setMouseTracking(self._showCurrentMouseUVPosition)
        self.setMinimumSize(400, 400)

    # SHAPE MANAGEMENT
    def addShapes(self, shapes):
        """Add a list of shapes to be drawn in the scene and refresh the view.
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
        """CLear a list of shapes from the view

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

    def setTextureShape(self, shape):
        """Set the shape used to draw the texture map in the view.

        Args:
            shape (shape.TextureShape | None):
                The shape to draw for the texture, or None if you want to remove the current one.
        """
        self._textureShape = shape
        if self._showTexture:
            self.update()

    def clear(self, removeTexture=False):
        """Clear all the shapes drawn in the view.

        Args:
            removeTexture (bool):
                If true, removes the shape used to draw the texture in the view.
        """
        if not self._shapes and (removeTexture and not self._textureShape):
            return
        self._shapes = []
        if removeTexture:
            self._textureShape = None
        self.update()

    # VIEW ACTIONS
    def setGridVisibility(self, visible):
        """Set the visible state of the grid lines and numbers in the view."""
        visible = bool(visible)
        if self._showGrid != visible:
            self._showGrid = visible
            self.update()

    def setMouseUVPositionDisplay(self, visible):
        """Set the visible state of the uv position at the current mouse position in the bottom left of the widget."""
        visible = bool(visible)
        if self._showCurrentMouseUVPosition != visible:
            self._showCurrentMouseUVPosition = visible
            self.setMouseTracking(visible)
            self.update()

    def setUVEdgeBoundaryHighlight(self, visible):
        """Set the display of uv edge boundary highlights."""
        visible = bool(visible)
        if self._showUVEdgeBoundaryHighlight != visible:
            self._showUVEdgeBoundaryHighlight = visible
            self.update()

    def setTextureVisible(self, visible):
        """Set the visible state of the texture shape."""
        visible = bool(visible)
        if self._showTexture != visible:
            self._showTexture = visible
            # Only need to do an update if an actual texture shape exists.
            if self._textureShape:
                self.update()

    def focusOnBBox(self):
        """Focus the viewer on the bbox surounding all the currently displayed shapes."""
        if not self._shapes:
            self._camera.focus(0.0, 1.0, 1.0, 0.0)
        else:
            bbox = None
            for _shape in self._shapes:
                if bbox is None:
                    bbox = _shape.bbox()
                else:
                    bbox.updateWithBBox(_shape.bbox())
            self._camera.focus(bbox.xMin, bbox.xMax, bbox.yMax, bbox.yMin)
        self.update()

    def changeBackgroundColor(self, color):
        """Change the background color used in the viewer.

        Args:
            tuple(int, int, int, int):
                RGBA values of the color to set as the background color.
        """
        if not isinstance(color, (list, tuple)) or len(color) != 4:
            raise RuntimeError(
                "Invalid color value to set %s. Must be list or set of 4 integers.",
                color,
            )

        if color != self._backgroundColor:
            self._backgroundColor = color
            self.update()

    # QT EVENTS
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_F:
            self.focusOnBBox()
        QtWidgets.QOpenGLWidget.keyPressEvent(self, event)

    def mousePressEvent(self, event):
        """Override to add custom state handling."""
        if not self._activeState:
            state = states.stateFromEvent(event)
            if state:
                self._activeState = state(
                    event, self._camera, self.width(), self.height()
                )
        self.setFocus()

    def mouseMoveEvent(self, event):
        """Override to add custom state handling."""
        if (
            self._activeState and self._activeState.update(event)
        ) or self._showCurrentMouseUVPosition:
            self.update()

    def mouseReleaseEvent(self, event):
        """Override to add custom state handling."""
        if self._activeState and self._activeState.shouldDisable(event.button()):
            self._activeState = None
        QtWidgets.QOpenGLWidget.mouseReleaseEvent(self, event)

    def wheelEvent(self, event):
        """Override to add custom GL zoom."""
        if not self._activeState:
            pos = event.pos()
            glCoords = self._camera.mapScreenToGl([pos.x(), pos.y()])
            worldCoords = self._camera.mapGlToWorld(glCoords)
            delta = event.angleDelta().y()
            zoomAmount = 1.0 + (delta and delta // abs(delta)) * 0.03
            self._camera.zoom(worldCoords, zoomAmount)
            self.update()
        self.setFocus()

    # GL EVENTS
    def initializeGL(self):
        """Setup GL objects for the view ready for drawing."""
        self._backgroundGrid = shape.Grid()
        self._camera = camera.Camera2D(self.width(), self.height())
        self._shader = shader.LineShader()
        self._painter = QtGui.QPainter()

        self._gridNumbersFont = QtGui.QFont()
        self._gridNumbersFont.setPointSize(8)
        self._uvInfoFont = QtGui.QFont()
        self._uvInfoFont.setPointSize(12)

    def resizeGL(self, width, height):
        """Resize the GL viewport and update the camera with the new dimensions."""
        GL.glViewport(0, 0, width, height)
        self._camera.resize(width, height)

    def paintGL(self):
        """Paint all the GL objects in the scene."""
        self._painter.begin(self)

        self._painter.beginNativePainting()
        GL.glClearColor(*self._backgroundColor)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        projectionMatrix = self._camera.glProjectionMatrix()

        # Draw texture
        if self._showTexture and self._textureShape:
            self._textureShape.draw(projectionMatrix)

        # Setup the shader used for both the grid and uv shapes.
        self._shader.use()
        self._shader.setMatrix4f("viewMatrix", projectionMatrix)

        # Draw grid
        if self._showGrid:
            self._backgroundGrid.draw(self._shader)

        # Draw UVs
        for _shape in self._shapes:
            _shape.draw(self._shader, drawBoundaries=self._showUVEdgeBoundaryHighlight)
        self._painter.endNativePainting()

        # Draw text
        if self._showGrid:
            self._drawText(self._painter)
        if self._showCurrentMouseUVPosition:
            self._drawMouseUVPosition(self._painter)
        self._painter.end()

    def _drawText(self, painter):
        """Paint the grid values in the scene."""
        originCoord = self._camera.mapWorldToScreen([0.0, 0.0])
        offsetCoord = self._camera.mapWorldToScreen([0.1, 0.1])

        width = offsetCoord[0] - originCoord[0]
        height = originCoord[1] - offsetCoord[1]
        doubleWidth = width * 2.0
        # Offset x a little to prevent intersection with the vertical grid line
        originX = originCoord[0] + width / 20.0
        originY = originCoord[1] - height

        def drawText(increment, xAxis=True):
            offset = float(increment) / 10.0
            if xAxis:
                left = originX + increment * width
                top = originY
            else:
                left = originX
                top = originY - increment * height

            text = str(offset)
            painter.drawText(
                left,
                top,
                doubleWidth,
                height,
                QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom,
                text,
            )

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
        """Draw the corresponding uv position from the current mouse position over the widget."""
        cursor = QtGui.QCursor()
        position = self.mapFromGlobal(cursor.pos())
        uvPos = self._camera.mapScreenToWorld([position.x(), position.y()])
        displayString = "UV: %.3f, %.3f" % (uvPos[0], uvPos[1])

        painter.setPen(QtCore.Qt.white)
        painter.setFont(self._uvInfoFont)
        painter.drawText(
            5,
            self.height() - 40,
            200,
            40,
            QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom,
            displayString,
        )


class ViewerConfiguration:
    """Class containing configuration for the viewer."""

    def __init__(self):
        self.displayTexture = False
        self.displayGrid = True
        self.displayUVBorder = False
        self.displayUVPos = False
