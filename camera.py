import numpy as np


class Camera2D:
    def __init__(self, width, height):
        self._projMat = None
        self._projMat_aspectRatio = None
        self._invProj = None
        self._aspectRatio = width / height
        self._focusBuffer = 0.1
        self.focus(0, 1, 1, 0)

    def focus(self, left, right, top, bottom):
        targetWidth = (right - left)
        targetWidth += targetWidth * self._focusBuffer
        targetHeight = (top - bottom)
        targetHeight += targetHeight * self._focusBuffer
        targetAspectRatio = targetWidth / targetHeight

        if targetAspectRatio >= self._aspectRatio:
            left = -self._aspectRatio / targetAspectRatio * targetWidth / 2.0
            right = self._aspectRatio / targetAspectRatio * targetWidth / 2.0
            top = targetHeight / 2.0
            bottom = -targetHeight / 2.0
        else:
            left = -targetWidth / 2.0
            right = targetWidth / 2.0
            top = targetAspectRatio / self._aspectRatio * targetHeight / 2.0
            bottom = -targetAspectRatio / self._aspectRatio * targetHeight / 2.0

        projMat = self.createProjectionMatrix(left, right, top, bottom)
        self.setProjectionMatrix(projMat)

    def pan(self, xOffset, yOffset):
        transformationMatrix = self.createTransformationMatrix(xOffset, yOffset)
        self.setProjectionMatrix(np.matmul(self._projMat, transformationMatrix))

    def reset(self):
        self.setProjectionMatrix(self.createProjectionMatrix(-0.1, 1.1, 1.1, -0.1))

    @staticmethod
    def screenToGlCoord(coord):
        return [(coord[0] - 0.5) * 2, (coord[1] - 0.5) * -2]

    def screenToWorldCoord(self, coord):
        glCoord = self.screenToGlCoord(coord)
        glScreenPosition = np.array([glCoord[0], glCoord[1], 0, 1])
        return self._invProj.dot(glScreenPosition)[:2]

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
        self._invProj = np.matrix.transpose(np.linalg.inv(self._projMat))

    def _applyAspectRatioToMatrix(self, matrix):
        matrix[1][1] *= self._aspectRatio
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
