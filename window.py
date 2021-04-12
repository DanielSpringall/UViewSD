import numpy as np
from camera import Camera2D
from shape import Shape
from OpenGL import GL
from PySide2.QtWidgets import QOpenGLWidget, QApplication
from PySide2.QtCore import Qt


class OpenGLWidget(QOpenGLWidget):
    def __init__(self, *args, **kwargs):
        QOpenGLWidget.__init__(self, *args, **kwargs)

        self._updateTranslate = False
        self._updateScale = False
        self._prevMousePos = None

        self._shapes = []
        self._camera = None
        self.setGeometry(100, 100, 400, 400)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_R:
            self._camera.reset()
            self.update()

    def mouseMoveEvent(self, event):
        pos = event.pos()
        mousePos = np.array((pos.x(), pos.y()))
        if self._updateTranslate:
            xTransform = (mousePos[0] - self._prevMousePos[0]) * 2
            yTransform = (self._prevMousePos[1] - mousePos[1]) * 2
            self._camera.pan(np.array((xTransform, yTransform), dtype=np.float32))
            self._prevMousePos = mousePos
            self.update()
        if self._updateScale:
            dist = np.linalg.norm(self._prevMousePos - mousePos)
            self._camera.zoom(dist)
            self.update()

    def mousePressEvent(self, event):
        if QApplication.keyboardModifiers() == Qt.AltModifier:
            pos = event.pos()
            self._prevMousePos = np.array((pos.x(), pos.y()))
            if event.button() == Qt.MiddleButton:
                self._updateTranslate = True
            elif event.button() == Qt.RightButton:
                self._updateScale = True
                self._camera.beginDynamicZoom()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._updateTranslate = False
        if event.button() == Qt.RightButton:
            self._updateScale = False

    def wheelEvent(self, event):
        pos = event.pos()
        mousePos = np.array((pos.x() * 2, (self.size().height() - pos.y()) * 2))
        delta = event.angleDelta().y()
        zoomAmount = (delta and delta // abs(delta)) * 0.05
        self._camera.zoom(mousePos, zoomAmount)
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
