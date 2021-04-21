import numpy as np
from camera import Camera2D
import shape
import states
from OpenGL import GL
from PySide2.QtWidgets import QOpenGLWidget, QApplication
from PySide2.QtGui import QPainter, QColor
from PySide2.QtCore import Qt, QRect, QPoint, QSize


class ViewerWidget(QOpenGLWidget):
    def __init__(self, *args, **kwargs):
        QOpenGLWidget.__init__(self, *args, **kwargs)

        self._painter = None
        self._activeState = None
        self._background = None
        self._shapes = []
        self._camera = None
        self.setGeometry(850, 400, 800, 800)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F:
            self._camera.focus(0, 1, 1, 0)
            self.update()

    def mousePressEvent(self, event):
        if not self._activeState:
            state = states.stateFromEvent(event)
            if state:
                self._activeState = state(event, self._camera, self.width(), self.height())

    def mouseMoveEvent(self, event):
        if self._activeState and self._activeState.update(event):
            self.update()

    def mouseReleaseEvent(self, event):
        if self._activeState and self._activeState.shouldDisable(event.button()):
            self._activeState = None

    def wheelEvent(self, event):
        if self._activeState:
            return

        pos = event.pos()
        screenCoords = [pos.x() / self.width(), pos.y() / self.height()]
        delta = event.angleDelta().y()
        zoomAmount = 1 + (delta and delta // abs(delta)) * 0.03
        self._camera.zoom(screenCoords, zoomAmount)
        self.update()

    def initializeGL(self):
        self._background = shape.Grid()
        self._camera = Camera2D(self.width(), self.height())
        self._shapes.append(shape.UVShape())
        self._painter = QPainter()

    def resizeGL(self, width, height):
        GL.glViewport(0, 0, width, height)
        self._camera.resize(width, height)

    def paintGL(self):
        self._painter.begin(self)

        self._painter.beginNativePainting()
        GL.glClearColor(0.3, 0.3, 0.3, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        projectionMatrix = self._camera.projectionMatrix()
        self._background.draw(projectionMatrix)
        for shape in self._shapes:
            shape.draw(projectionMatrix)
        self._painter.endNativePainting()

        self.drawText(self._painter)
        self._painter.end()

    def drawText(self, painter):
        screenCoord = [0.5, 0.5]

        originCoord = self._camera.worldToScreenCoord([0.0, 0.0])
        originCoord[0] = originCoord[0] * self.width()
        originCoord[1] = originCoord[1] * self.height()

        offsetCoord = self._camera.worldToScreenCoord([0.1, 0.1])
        offsetCoord[0] = offsetCoord[0] * self.width()
        offsetCoord[1] = offsetCoord[1] * self.height()

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
            painter.drawText(left, top, doubleWidth, height, Qt.AlignLeft | Qt.AlignBottom, text)

        painter.setPen(Qt.black)
        drawText(0)
        # Draw the rest of the text
        for i in range(1, shape.TOTAL_LINES + 1):
            drawText(i, xAxis=True)
            drawText(-i, xAxis=True)
            drawText(i, xAxis=False)
            drawText(-i, xAxis=False)


if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_UseDesktopOpenGL)
    app = QApplication([])
    widget = ViewerWidget()
    widget.show()
    app.exec_()
