import numpy as np
from camera import Camera2D
import shape
import states
from OpenGL import GL
from PySide2.QtWidgets import QOpenGLWidget, QApplication
from PySide2.QtGui import QPainter, QFont
from PySide2.QtCore import Qt


class OpenGLWidget(QOpenGLWidget):
    def __init__(self, *args, **kwargs):
        QOpenGLWidget.__init__(self, *args, **kwargs)

        self._activeState = None
        self._background = None
        self._shapes = []
        self._camera = None
        self.setGeometry(850, 400, 800, 800)
        self.setFixedSize(800, 800)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_R:
            self._camera.reset()
            self.update()
        elif event.key() == Qt.Key_Up:
            self._camera.zoom((0.5, 0.5), 0.5)
            self.update()
        elif event.key() == Qt.Key_Down:
            self._camera.zoom((0.5, 0.5), 2)
            self.update()
        elif event.key() == Qt.Key_Left:
            self._camera.pan(-1, 0)
            self.update()
        elif event.key() == Qt.Key_Right:
            self._camera.pan(1, 0)
            self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.pos()
        elif not self._activeState:
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

    def drawText(self):
        return
        painter = QPainter()
        painter.begin(self)
        painter.setPen(Qt.black)
        painter.setFont(QFont("Arial", 10))
        painter.drawText(0, 0, 100, 100, Qt.AlignLeft, "Test");
        painter.end()

    def initializeGL(self):
        self._background = shape.Grid()
        self._camera = Camera2D(self.width(), self.height())

    def resizeGL(self, width, height):
        GL.glViewport(0, 0, width, height)
        self._camera.setImageSize(width, height)

    def paintGL(self):
        GL.glClearColor(0.3, 0.3, 0.3, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        projectionMatrix = self._camera.projectionMatrix()
        self._background.draw(projectionMatrix)
        for shape in self._shapes:
            shape.draw(projectionMatrix)
        # self._selectionMarquee.draw()
        # self.drawText()


if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_UseDesktopOpenGL)
    app = QApplication([])
    widget = OpenGLWidget()
    widget.show()
    app.exec_()
