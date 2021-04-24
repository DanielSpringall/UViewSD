from OpenGL import GL
from PySide2 import QtWidgets, QtGui, QtCore
import numpy as np
from pxr import Usd

import shape
import states
import camera


class ViewerWidget(QtWidgets.QOpenGLWidget):
    def __init__(self, *args, **kwargs):
        QtWidgets.QOpenGLWidget.__init__(self, *args, **kwargs)

        self._painter = None
        self._activeState = None
        self._background = None
        self._shapes = []
        self._camera = None

    def clear(self):
        for shape in self._shapes:
            # Do something to shapes?
            pass
        self._shapes = []

    def addShape(self, shape):
        self._shapes.append(shape)
        self.update()

    def removeShape(self):
        pass

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_F:
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

    def addShape(self, shape):
        self._shapes.append(shape)
        self.update()

    def removeShape(self, shape):
        pass

    def initializeGL(self):
        self._background = shape.Grid()
        self._camera = camera.Camera2D(self.width(), self.height())
        self._painter = QtGui.QPainter()

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
            painter.drawText(left, top, doubleWidth, height, QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom, text)

        painter.setPen(QtCore.Qt.black)
        drawText(0)
        # Draw the rest of the text
        for i in range(1, shape.TOTAL_LINES + 1):
            drawText(i, xAxis=True)
            drawText(-i, xAxis=True)
            drawText(i, xAxis=False)
            drawText(-i, xAxis=False)


class Window(QtWidgets.QMainWindow):
    def __init__(self, parent, stage=None, *args, **kwargs):
        QtWidgets.QMainWindow.__init__(self, parent=parent, *args, **kwargs)
        self._view = ViewerWidget()
        self.setCentralWidget(self._view)

        self.setGeometry(850, 400, 800, 800)

        self._stage = stage

    def addPrimPath(self, primPath, override=False):
        prim = self._stage.GetPrimAtPath(primPath)
        if not prim.IsValid():
            raise RuntimeError("No valid prim at path: {}".format(primName))
        return self.addPrim(prim, override)

    def addPrim(self, prim, override=False):
        if override:
            self._view.clear()

        faceVertCountAttr, uvIndexAttr, uvAttr = self._getRelevantAttributesFromPrim(prim)
        if not (faceVertCountAttr and uvIndexAttr and uvAttr):
            return False

        faceVertCountList = faceVertCountAttr.Get()
        uvIndices = uvIndexAttr.Get()
        uvValues = uvAttr.Get()

        consumedIndices = 0
        uvLines = []
        for faceVertCount in faceVertCountList:
            faceUVs = []
            for i in range(faceVertCount):
                faceVertIndex = consumedIndices + i
                uvIndex = uvIndices[faceVertIndex]
                faceUVs.append(uvValues[uvIndex])
            lines = [
                faceUVs[0], faceUVs[1], faceUVs[1], faceUVs[2], faceUVs[2], faceUVs[3], faceUVs[3], faceUVs[0]
            ]
            flattenedlines = [uv for uvData in lines for uv in uvData]
            uvLines.extend(flattenedlines)
            consumedIndices += faceVertCount

        self._view.addShape(shape.UVShape(uvLines))

    @staticmethod
    def _getRelevantAttributesFromPrim(prim):
        faceVertCountAttr = prim.GetAttribute("faceVertexCounts")
        uvIndexAttr = prim.GetAttribute("primvars:st:indices")
        uvAttr = prim.GetAttribute("primvars:st")
        return faceVertCountAttr, uvIndexAttr, uvAttr


def run(usdviewApi=None, primPath=None):
    primPath = "/Kitchen_set/Props_grp/DiningTable_grp/KitchenTable_1/Geom/Top"

    if usdviewApi:
        stage = usdviewApi.stage
        parent = usdviewApi.qMainWindow
    else:
        stage = Usd.Stage.Open("C:\\Libraries\\USD\\share\\usd\\kitchenSet\\Kitchen_set.usd")
        parent = None

    window = Window(parent=parent, stage=stage)
    window.show()
    window.addPrimPath(primPath)

    return window


if __name__ == "__main__":
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseDesktopOpenGL)
    app = QtWidgets.QApplication([])
    window = run()
    app.exec_()
