import numpy as np
from camera import Camera2D
from shape import Shape
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
        self.setGeometry(100, 100, 400, 400)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_R:
            self._camera.reset()
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
        mousePos = np.array((pos.x() * 2, (self.size().height() - pos.y()) * 2))
        delta = event.angleDelta().y()
        zoomAmount = (delta and delta // abs(delta)) * 0.05
        self._camera.zoom(mousePos, zoomAmount, additive=True)
        self.update()

    def initializeGL(self):
        backgroundGrid = Shape()
        self._shapes.append(backgroundGrid)

        windowSize = self.size()
        self._camera = Camera2D(windowSize.width(), windowSize.height())

    def paintGL(self):
        GL.glClearColor(0.2, 0.3, 0.3, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        windowSize = self.size()
        self._camera.setImageSize(windowSize.width(), windowSize.height())
        GL.glViewport(0, 0, int(self._camera._width), int(self._camera._height))

        for shape in self._shapes:
            shape.draw(self._camera)


if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_UseDesktopOpenGL)
    app = QApplication([])
    widget = OpenGLWidget()
    widget.show()
    app.exec_()
