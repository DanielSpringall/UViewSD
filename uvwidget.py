from PySide2 import QtWidgets, QtGui, QtCore
from OpenGL import GL

import shape
import states
import camera
import logging

logger = logging.getLogger(__name__)


class ViewerWidget(QtWidgets.QOpenGLWidget):
    def __init__(self, *args, **kwargs):
        QtWidgets.QOpenGLWidget.__init__(self, *args, **kwargs)

        self._painter = None
        self._uvDataFont = None

        self._activeState = None
        self._backgroundGrid = None
        self._shapes = {}
        self._camera = None

        self._showGrid = True
        self._showCurrentMouseUVPosition = True

        self.setMouseTracking(self._showCurrentMouseUVPosition)

    # SHAPE MANAGEMENT
    def addShapes(self, shapes):
        """ Add a list of shapes to be drawn in the scene and refresh the view.
        Existing shapes with the same name will be overridden.

        Args:
            shapes (dict{name: shape.UVShape}):
                Dictionary of the shapes to draw. Keys are the identifiers for each shape, values are the shape data.
        """
        for shapeName in shapes:
            self._shapes[shapeName] = shapes[shapeName]
        self.update()

    def removeShapes(self, shapeNames):
        """ CLear a list of shapes from the view
        
        Args:
            shapeNames (list[str]): Names of the shapes to remove from the view.
        """
        if not self._shapes:
            return

        shapeRemoved = False
        for shapeName in shapeNames:
            if shapeName not in self._shapes:
                continue
            del self._shapes[shapeName]
            shapeRemoved = True

        if shapeRemoved:
            self.update()

    def clear(self):
        """ Clear all the current shapes drawn in the view. """
        if not self._shapes:
            return
        self._shapes = {}
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
        shapes = list(self._shapes.values())
        if not shapes:
            self._camera.focus(0, 1, 1, 0)
        else:
            bbox = None
            for _shape in shapes:
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

    def mousePressEvent(self, event):
        if not self._activeState:
            state = states.stateFromEvent(event)
            if state:
                self._activeState = state(event, self._camera, self.width(), self.height())

    def mouseMoveEvent(self, event):
        if self._activeState and self._activeState.update(event):
            self.update()
        if self._showCurrentMouseUVPosition:
            self.update()

    def mouseReleaseEvent(self, event):
        if self._activeState and self._activeState.shouldDisable(event.button()):
            self._activeState = None

    def wheelEvent(self, event):
        if self._activeState:
            return

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
        for shape in self._shapes.values():
            shape.draw(projectionMatrix)
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
        drawText(0)
        # Draw the rest of the text
        for i in range(1, self._backgroundGrid.TOTAL_LINES + 1):
            drawText(i, xAxis=True)
            drawText(-i, xAxis=True)
            drawText(i, xAxis=False)
            drawText(-i, xAxis=False)

    def _drawMouseUVPosition(self, painter):
        """ Draw the corresponding uv position from the current mouse position. """
        cursor = QtGui.QCursor()
        position = self.mapFromGlobal(cursor.pos())
        uvPos = self._camera.mapScreenToWorld([position.x(), position.y()])
        displayString = "UV: %.3f, %.3f" % (uvPos[0], uvPos[1])

        painter.setPen(QtCore.Qt.white)
        if self._uvDataFont is None:
            self._uvDataFont = QtGui.QFont()
            self._uvDataFont.setPointSize(14)
        painter.setFont(self._uvDataFont)
        painter.drawText(10, self.height() - 60, 200, 50, QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom, displayString)
