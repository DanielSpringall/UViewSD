import numpy as np
from camera import Camera2D
import shape
import states
from OpenGL import GL
from PySide2.QtWidgets import QOpenGLWidget, QApplication
from PySide2.QtCore import Qt


class OpenGLWidget(QOpenGLWidget):
    def __init__(self, *args, **kwargs):
        QOpenGLWidget.__init__(self, *args, **kwargs)

        self._activeState = None
        self._shapes = []
        self._camera = None
        self.setGeometry(850, 400, 800, 800)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_R:
            self._camera.reset()
            self.update()
        elif event.key() == Qt.Key_Up:
            pos = np.array((400, 400))
            self._camera.zoom(pos, 0.1)
            self.update()
        elif event.key() == Qt.Key_Down:
            pos = np.array((400, 400))
            self._camera.zoom(pos, -0.1)
            self.update()
        elif event.key() == Qt.Key_Left:
            pos = np.array((200, 200))
            self._camera.zoom(pos, -0.1)
            self.update()
        elif event.key() == Qt.Key_Right:
            pos = np.array((200, 200))
            self._camera.zoom(pos, 0.1)
            self.update()

    def mousePressEvent(self, event):
        if not self._activeState:
            newState = states.getState(event)
            if newState:
                self._activeState = newState(event, self._camera)

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
        # mousePos = np.array((pos.x() * 2, (self.size().height() - pos.y()) * 2))
        mousePos = np.array((self.width(), self.height()))
        delta = event.angleDelta().y()
        zoomAmount = (delta and delta // abs(delta)) * self._camera._zoom * 0.03
        self._camera.zoom(mousePos, zoomAmount)
        self.update()

    def initializeGL(self):
        # backgroundGrid = shape.TestShape()
        # self._shapes.append(backgroundGrid)
        backgroundGrid = shape.Grid()
        self._shapes.append(backgroundGrid)
        self._camera = Camera2D(self.width(), self.height())

    def paintGL(self):
        width = self.width()
        height = self.height()
        GL.glViewport(0, 0, width, height)
        self._camera.setImageSize(width, height)

        GL.glClearColor(0.3, 0.3, 0.3, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)
        for shape in self._shapes:
            shape.draw(self._camera)


if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_UseDesktopOpenGL)
    app = QApplication([])
    widget = OpenGLWidget()
    widget.show()
    app.exec_()
