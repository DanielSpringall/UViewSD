import numpy as np


class Camera2D:
    def __init__(self, width, height):
        self._projectionMatrix = None
        self._inverseProjectionMatrix = None
        self.setProjectionMatrix(
            self.createProjectionMatrix(-0.1, 1.1, 1.1, -0.1)
        )

    def pan(self, xOffset, yOffset):
        transformationMatrix = self.createTransformationMatrix(xOffset, yOffset)
        self.setProjectionMatrix(np.matmul(self._projectionMatrix, transformationMatrix))

    def reset(self):
        self.setProjectionMatrix(
            self.createProjectionMatrix(-0.1, 1.1, 1.1, -0.1)
        )

    @staticmethod
    def glToScreenCoord(coord):
        return [coord[0] / 2 + 0.5, coord[1] / -2 + 0.5]

    @staticmethod
    def screenToGlCoord(coord):
        return [(coord[0] - 0.5) * 2, (coord[1] - 0.5) * -2]

    def screenToWorldCoord(self, coord):
        glCoord = self.screenToGlCoord(coord)
        glScreenPosition = np.array([glCoord[0], glCoord[1], 0, 1])
        return self._inverseProjectionMatrix.dot(glScreenPosition)[:2]

    def zoom(self, coord, amount):
        worldCoords = self.screenToWorldCoord(coord)
        transMat = np.matrix.transpose(Camera2D.createTransformationMatrix(-worldCoords[0], -worldCoords[1]))
        invTransMat = np.matrix.transpose(Camera2D.createTransformationMatrix(worldCoords[0], worldCoords[1]))
        projectionMatrix = np.matrix.transpose(self._projectionMatrix)
        self.setProjectionMatrix(np.matrix.transpose(self.scaleMatrix(projectionMatrix, amount, transMat, invTransMat)))

    @staticmethod
    def scaleMatrix(matrixToScale, amount, transMat, invTransMat):
        matrixToScale = np.matmul(matrixToScale, invTransMat)
        matrixToScale[0][0] *= amount
        matrixToScale[1][1] *= amount
        matrixToScale = np.matmul(matrixToScale, transMat)
        return matrixToScale

    def focus(self, left, right, top, bottom, width, height):
        pass

    def setImageSize(self, width, height):
        self._width = width
        self._height = height

    def setProjectionMatrix(self, matrix):
        self._projectionMatrix = matrix
        self._inverseProjectionMatrix = np.matrix.transpose(np.linalg.inv(matrix))

    def projectionMatrix(self):
        return np.matrix.flatten(self._projectionMatrix)

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
