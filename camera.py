import numpy as np


class Camera2D:
    def __init__(self, width, height):
        """ Camera class for generating and manipulating an orthographic projection matrix.

        Args:
            width (int): Screen width.
            height (int): Screen height.
        """
        self._aspectRatio = width / height

        # Cached projection matrix and matrices used for internal calculations
        self._projMat = None
        self._projMat_aspectRatio = None
        self._invProj_aspectRatio = None

        # Percentage of the Vertical/horizontal width to apply as a buffer when focusing
        self._focusBuffer = 0.1

        # Initial camera focus
        self.focus(0, 1, 1, 0)

    def focus(self, left, right, top, bottom):
        """ Focus the projection matrix to a given square denoted by left/right/top/bottom units.
        Will take the image width/height into account to ensure the focus region fits inside it.

        Args:
            left (float): The left unit in world space of the focus region.
            right (float): The right unit in world space of the focus region.
            top (float): The top unit in world space of the focus region.
            bottom (float): The bottom unit in world space of the focus region.
        """
        xBuffer = (right - left) * self._focusBuffer
        yBuffer = (top - bottom) * self._focusBuffer
        left -= xBuffer
        right += xBuffer
        top += yBuffer
        bottom -= yBuffer
        projMat = self.createProjectionMatrix(left, right, top, bottom)
        self.setProjectionMatrix(projMat)

    def pan(self, x=0, y=0):
        """ Pan the projection matrix.

        Args:
            x (float): The amount of translation along the x axis in world space units.
            y (float): The amount of translation along the y axis in world space units.
        """
        if x == 0 and y == 0:
            return

        transformationMatrix = self.createTransformationMatrix(x, y)
        self.setProjectionMatrix(np.matmul(self._projMat, transformationMatrix))

    @staticmethod
    def mapGlToScreen(coord):
        """ Map a GL screen co-ordinate to its corresponding Qt screen co-ordinate.

        Args:
            coord (list[float, float]): The GL screen co-ordinate to map from.
        Return:
            (list[float, float]): The Qt mapped screen co-ordinate.
        """
        return [coord[0] / 2 + 0.5, coord[1] / -2 + 0.5]

    @staticmethod
    def mapScreenToGl(coord):
        """ Map a Qt screen co-ordinate to its corresponding GL screen co-ordinate.

        Args:
            coord (list[float, float]): The Qt screen co-ordinate to map from.
        Return:
            (list[float, float]): The GL mapped screen co-ordinate.
        """
        return [(coord[0] - 0.5) * 2, (coord[1] - 0.5) * -2]

    def mapScreenToWorld(self, coord):
        """ Map a QT screen co-ordinate to its corresponding world co-ordinate.

        Args:
            coord (list[float, float]): The Qt screen co-ordinate to map from.
        Return:
            (list[float, float]): The mapped world co-ordinate.
        """
        return self.mapGlToWorld(self.mapScreenToGl(coord))

    def mapGlToWorld(self, coord):
        """ Map a GL screen co-ordinate to its corresponding world co-ordinate.

        Args:
            coord (list[float, float]): The GL screen co-ordinate to map from.
        Return:
            (list[float, float]): The mapped world co-ordinate.
        """
        glScreenPosition = np.array([coord[0], coord[1], 0.0, 1.0])
        return self._invProj_aspectRatio.dot(glScreenPosition)[:2]

    def mapWorldToScreen(self, coord):
        """ Map a world co-ordinate to its corresponding QT screen co-ordinate.

        Args:
            coord (list[float, float]): The world co-ordinate to map from.
        Return:
            (list[float, float]): The mapped Qt screen co-ordinate.
        """
        worldCoord = np.array([coord[0], coord[1], 0.0, 1.0])
        screenGlCoord = self._projMat_aspectRatio.dot(worldCoord)[:2]
        return self.mapGlToScreen(screenGlCoord)

    def zoom(self, coord, amount):
        """ Zoom the projection matrix around a given world co-ordinate.

        Args:
            coord (list[float, float]): World space co-ordinate to zoom on.
            amount (float): Value to multiply the current scale by. Value of 1.0 is the same as no scale.
        """
        self.setProjectionMatrix(self.scaleMatrixAroundPoint(self.projectionMatrix(), amount, coord))

    @classmethod
    def scaleMatrixAroundPoint(cls, matrixToScale, scaleAmount, coord, minScaleAmount=0.01):
        """ Utility method to uniformly scale a matrix around a given co-ordinate.

        Args:
            matrixToScale (np.matrix(4x4)): The matrix to scale.
            scaleAmount (float): The amount to multiply the current matrices scale by.
            coord (list[float, float]): The co-ordinate to scale the matrix around.
            minScaleAmount (float): The minimum scale allowed to help prevent flipping.
        """
        currentScaleAmount = matrixToScale[0][0]
        if scaleAmount == 1.0 or currentScaleAmount <= minScaleAmount:
            return matrixToScale

        resultingScaleAmount = currentScaleAmount * scaleAmount
        if resultingScaleAmount <= minScaleAmount:
            resultingScaleAmount = minScaleAmount

        if coord[0] == 0.0 and coord[1] == 0.0:
            matrixToScale[0][0] = resultingScaleAmount
            matrixToScale[1][1] = resultingScaleAmount
        else:    
            translationMatrix = cls.createTransformationMatrix(coord[0], coord[1])
            matrixToScale = matrixToScale.dot(translationMatrix)
            matrixToScale[0][0] = resultingScaleAmount
            matrixToScale[1][1] = resultingScaleAmount
            matrixToScale = matrixToScale.dot(np.linalg.inv(translationMatrix))

        return matrixToScale

    def resize(self, width, height):
        """ Resize the camera output image.

        Args:
            width (int): New screen width.
            height (int): New screen height.
        """
        newAspectRatio = float(width) / float(height)
        if newAspectRatio != self._aspectRatio:
            self._aspectRatio = newAspectRatio
            self.setProjectionMatrix(self._projMat)

    def setProjectionMatrix(self, matrix):
        """ Set the projection matrix for the camera.

        Args:
            matrix (np.matrix(4x4)): The projection matrix to set.
        """
        self._projMat = matrix

        aspectRatioMatrix = matrix.copy()
        aspectRatioMatrix[1][1] *= self._aspectRatio
        aspectRatioMatrix[3][1] *= self._aspectRatio
        self._projMat_aspectRatio = aspectRatioMatrix
        self._invProj_aspectRatio = np.linalg.inv(self._projMat_aspectRatio)

    def projectionMatrix(self):
        """ The current projectino matrix.

        Return:
            (np.matrix(4x4)): The current projection matrix.
        """
        return self._projMat_aspectRatio

    def glProjectionMatrix(self):
        """ Utility method to get the projectino matrix in a way that can be used by GL.

        Return:
            (float[16]): Flattened projection matrix.
        """
        return np.matrix.flatten(np.matrix.transpose(self.projectionMatrix()))

    @staticmethod
    def createProjectionMatrix(left, right, top, bottom):
        """ Utility method to generate a projection matrix from given focus region.

        Args:
            left (float): The left unit in world space of the focus region.
            right (float): The right unit in world space of the focus region.
            top (float): The top unit in world space of the focus region.
            bottom (float): The bottom unit in world space of the focus region.
        """
        xScale = 2.0 / (right - left)
        yScale = 2.0 / (top - bottom)

        xTransform = -((right + left) / (right - left))
        yTransform = -((top + bottom) / (top - bottom))

        projectionMat = np.identity(4)
        projectionMat[0][0] = xScale
        projectionMat[1][1] = yScale
        projectionMat[0][3] = xTransform
        projectionMat[1][3] = yTransform

        return projectionMat

    @staticmethod
    def createTransformationMatrix(x, y):
        """ Utility method to generate a 4x4 2D transformation matrix.

        Args:
            x (float): The transformation value on the x axis.
            y (float): The transformation value on the y axis.
        Return:
            (np.matrix(4x4)): Transformation matrix.
        """
        matrix = np.identity(4)
        matrix[0][3] = x
        matrix[1][3] = y
        return matrix

    @staticmethod
    def createScaleMatrix(scale):
        """ Utility method to generate a uniformly scaled 2D 4x4 matrix.

        Args:
            scale (float): The scale amount for the x and y axis.
        Return:
            (np.matrix(4x4)): Scale matrix.
        """
        matrix = np.identity(4)
        matrix[0][0] = scale
        matrix[1][1] = scale
        return matrix
