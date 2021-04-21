import numpy as np


class Camera2D:
    def __init__(self, width, height):
        self._projMat = None
        self._projMat_aspectRatio = None
        self._invProj_aspectRatio = None
        self._aspectRatio = width / height
        self._focusBuffer = 0.1
        self.focus(0, 1, 1, 0)

    def focus(self, left, right, top, bottom):
        xBuffer = (right - left) * self._focusBuffer
        yBuffer = (top - bottom) * self._focusBuffer
        left -= xBuffer
        right += xBuffer
        top += yBuffer
        bottom -= yBuffer
        projMat = self.createProjectionMatrix(left, right, top, bottom)
        self.setProjectionMatrix(projMat)

    def pan(self, xOffset, yOffset):
        transformationMatrix = self.createTransformationMatrix(xOffset, yOffset)
        self.setProjectionMatrix(np.matmul(self._projMat, transformationMatrix))

    @staticmethod
    def glToScreenCoord(coord):
        return [coord[0] / 2 + 0.5, coord[1] / -2 + 0.5]

    @staticmethod
    def screenToGlCoord(coord):
        return [(coord[0] - 0.5) * 2, (coord[1] - 0.5) * -2]

    def screenToWorldCoord(self, coord):
        glCoord = self.screenToGlCoord(coord)
        glScreenPosition = np.array([glCoord[0], glCoord[1], 0.0, 1.0])
        return self._invProj_aspectRatio.dot(glScreenPosition)[:2]

    def worldToScreenCoord(self, coord):
        worldCoord = np.array([coord[0], coord[1], 0.0, 1.0])
        screenGlCoord = np.matrix.transpose(self._projMat_aspectRatio).dot(worldCoord)[:2]
        return self.glToScreenCoord(screenGlCoord)

    def zoom(self, coord, amount):
        worldCoords = self.screenToWorldCoord(coord)
        transMat = np.matrix.transpose(Camera2D.createTransformationMatrix(-worldCoords[0], -worldCoords[1]))
        invTransMat = np.matrix.transpose(Camera2D.createTransformationMatrix(worldCoords[0], worldCoords[1]))
        projectionMatrix = np.matrix.transpose(self._projMat)
        self.setProjectionMatrix(np.matrix.transpose(self.scaleMatrix(projectionMatrix, amount, transMat, invTransMat)))

    @staticmethod
    def scaleMatrix(matrixToScale, amount, transMat, invTransMat, minimumScale=0.01):
        matrixToScale = np.matmul(matrixToScale, invTransMat)
        scale = matrixToScale[0][0] * amount
        scale = scale if scale >= minimumScale else minimumScale
        matrixToScale[0][0] = scale
        matrixToScale[1][1] = scale
        matrixToScale = np.matmul(matrixToScale, transMat)
        return matrixToScale

    def resize(self, width, height):
        self._aspectRatio = float(width) / float(height)
        self.setProjectionMatrix(self._projMat)

    def setProjectionMatrix(self, matrix):
        self._projMat = matrix
        self._projMat_aspectRatio = self._applyAspectRatioToMatrix(matrix.copy())
        self._invProj_aspectRatio = np.matrix.transpose(np.linalg.inv(self._projMat_aspectRatio))

    def _applyAspectRatioToMatrix(self, matrix):
        matrix[1][1] *= self._aspectRatio
        matrix[3][1] *= self._aspectRatio
        return matrix

    def projectionMatrix(self):
        return np.matrix.flatten(self._projMat_aspectRatio)

    @staticmethod
    def createProjectionMatrix(left, right, top, bottom):
        xScale = 2.0 / (right - left)
        yScale = 2.0 / (top - bottom)

        xTransform = -((right + left) / (right - left))
        yTransform = -((top + bottom) / (top - bottom))

        projectionMat = np.identity(4)
        projectionMat[0][0] = xScale
        projectionMat[1][1] = yScale
        projectionMat[3][0] = xTransform
        projectionMat[3][1] = yTransform

        return projectionMat

    @staticmethod
    def createTransformationMatrix(xTransform, yTransform):
        matrix = np.identity(4)
        matrix[3][0] = xTransform
        matrix[3][1] = yTransform
        return matrix
