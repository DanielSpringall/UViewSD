import numpy as np


class Camera2D:
    def __init__(self, width, height):
        self._originalWidth = width
        self._originalHeight = height
        self._width = width
        self._height = height

        self._left = -1.1
        self._right = 1.1
        self._top = 1.1
        self._bottom = -1.1

        self._translation = np.array((0, 0), dtype=np.float32)
        self._minZoom = 0.0001
        self._zoom = 1

    def pan(self, translation):
        self._translation += np.array(
            (translation[0] / self._originalWidth,
             translation[1] / self._originalHeight), 
            dtype=np.float32
        )

    def reset(self):
        self._translation = np.array((0, 0), dtype=np.float32)
        self._zoom = 1
        self._height = self._originalHeight
        self._width = self._originalWidth

    def zoom(self, pos, amount):
        if self._zoom + amount <= self._minZoom:
            return

        targetWidth = self._width - (self._width * amount)
        targetHeight = self._height - (self._height * amount)

        tx = (targetWidth - self._width) * (pos[0] / self._width) / self._width
        ty = (targetHeight - self._height) * (pos[1] / self._height) / self._height

        self._translation += np.array((tx , ty), dtype=np.float32)
        self._zoom = self._zoom + amount

    def focus(self, left, right, top, bottom, width, height):
        pass

    def setImageSize(self, width, height):
        self._width = width
        self._height = height

    def projectionMatrix(self):
        widthRatio = self._width / self._originalWidth
        heightRatio = self._height / self._originalHeight

        xScale = (2.0 / (self._right - self._left) / widthRatio) * self._zoom
        yScale = (2.0 / (self._top - self._bottom) / heightRatio) * self._zoom
        zScale = 1.0

        xTransform = -(self._right + self._left) / (self._right - self._left)
        xTransform += self._translation[0] / widthRatio # x translation
        yTransform = -(self._top + self._bottom) / (self._top - self._bottom)
        yTransform -= 2 * ((self._originalHeight - self._height) / self._height) # y translation
        yTransform += self._translation[1] / heightRatio # anchor y offset to the top left of the image
        zTransform = 0

        return np.array([
            xScale,     0,          0,          0,
            0,          yScale,     0,          0,
            0,          0,          zScale,     0,
            xTransform, yTransform, zTransform, 1.0,
        ], dtype=np.float32)
