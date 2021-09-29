# Copyright 2021 by Daniel Springall.
# This file is part of UViewSD, and is released under the "MIT License Agreement".
# Please see the LICENSE file that should have been included as part of this package.
import numpy as np


class Camera2D:
    def __init__(self, width, height):
        """Camera class for generating and manipulating an orthographic projection matrix.

        Args:
            width (int): Screen width.
            height (int): Screen height.
        """
        self._screenWidth = float(width)
        self._screenHeight = float(height)
        self._screenAspectRatio = self._screenWidth / self._screenHeight
        # Cached focus region used to prevent jittering when consecutively calling resize. e.g. during user window resize.
        self._initResizeFocusRegion = None
        self._defaultBufferScale = 0.1

        # Cached projection matrix and matrices used for internal calculations
        self._projMat = None
        self._invProjMat = None

        # Initial camera focus
        self.focus(0.0, 1.0, 1.0, 0.0)

    def focus(self, left, right, top, bottom, bufferScale=None, clearFocusCache=True):
        """Focus the projection matrix to a given square denoted by left/right/top/bottom units.
        All units are interpreted as world unites. Will take the image width/height into
        account to ensure the focus region fits inside it.

        Args:
            left (float): The left unit in world space of the focus region.
            right (float): The right unit in world space of the focus region.
            top (float): The top unit in world space of the focus region.
            bottom (float): The bottom unit in world space of the focus region.
            bufferScale (float | None): Value multiplied by width/height to add as horizontal/vertical buffer
                                        to the focus region. If None, fall back on camera default buffer scale.
            clearFocusCache (bool): If True, clear the cached focus region used during resize.
        """
        if bufferScale is None:
            bufferScale = self._defaultBufferScale

        width = float(right - left)
        height = float(top - bottom)
        aspectRatio = width / height

        if self._screenAspectRatio >= aspectRatio:
            halfWidth = width / 2.0
            xMid = float(left) + halfWidth
            scaledHalfWidth = float(abs(self._screenAspectRatio / aspectRatio * halfWidth))
            left = xMid - scaledHalfWidth
            right = xMid + scaledHalfWidth
        else:
            halfHeight = height / 2.0
            yMid = float(bottom) + halfHeight
            scaledHalfHeight = float(abs(aspectRatio / self._screenAspectRatio * halfHeight))
            top = yMid + scaledHalfHeight
            bottom = yMid - scaledHalfHeight

        if bufferScale:
            xBuffer = float(right - left) * bufferScale
            yBuffer = float(top - bottom) * bufferScale
            left -= xBuffer
            right += xBuffer
            top += yBuffer
            bottom -= yBuffer

        projMat = self.createProjectionMatrix(left, right, top, bottom)
        self.setProjectionMatrix(projMat, clearFocusCache)

    def getFocusRegion(self):
        """Extract the focus region from the cameras projection matrix.

        Returns:
            tuple(float, float, float, float): Left, right, top, bottom values of the focus region.
        """
        projectionMat = self.projectionMatrix()
        xScale = float(projectionMat[0][0])
        yScale = float(projectionMat[1][1])
        xTransform = float(projectionMat[0][3])
        yTransform = float(projectionMat[1][3])

        left = -(1.0 + xTransform) / xScale
        right = (1.0 - xTransform) / xScale
        top = (1.0 - yTransform) / yScale
        bottom = -(1.0 + yTransform) / yScale

        return (left, right, top, bottom)

    def pan(self, x=0.0, y=0.0):
        """Pan the projection matrix.

        Args:
            x (float): The amount of translation along the x axis in world space units.
            y (float): The amount of translation along the y axis in world space units.
        """
        if x == 0.0 and y == 0.0:
            return

        transformationMatrix = self.createTransformationMatrix(-x, -y)
        self.setProjectionMatrix(np.matmul(self._projMat, transformationMatrix))

    def mapGlToScreen(self, coord):
        """Map a GL screen co-ordinate to its corresponding Qt screen co-ordinate for the current screen.

        Args:
            coord (list[float, float]): The GL screen co-ordinate to map from.
        Returns:
            list[float, float]: The Qt mapped screen co-ordinate.
        """
        return [
            (float(coord[0]) / 2.0 + 0.5) * self._screenWidth,
            (float(coord[1]) / -2.0 + 0.5) * self._screenHeight,
        ]

    def mapScreenToGl(self, coord):
        """Map a Qt screen co-ordinate to its corresponding GL screen co-ordinate for the current screen.

        Args:
            coord (list[float, float]): The Qt screen co-ordinate to map from.
        Returns:
            list[float, float]: The GL mapped screen co-ordinate.
        """
        return [
            float(coord[0]) / self._screenWidth * 2.0 - 1.0,
            (float(coord[1]) / self._screenHeight - 0.5) * -2.0,
        ]

    def mapScreenToWorld(self, coord):
        """Map a QT screen co-ordinate to its corresponding world co-ordinate.

        Args:
            coord (list[float, float]): The Qt screen co-ordinate to map from.
        Return:
            (list[float, float]): The mapped world co-ordinate.
        """
        return self.mapGlToWorld(self.mapScreenToGl(coord))

    def mapGlToWorld(self, coord):
        """Map a GL screen co-ordinate to its corresponding world co-ordinate.

        Args:
            coord (list[float, float]): The GL screen co-ordinate to map from.
        Returns:
            list[float, float]: The mapped world co-ordinate.
        """
        glScreenPosition = np.array([coord[0], coord[1], 0.0, 1.0])
        return self._invProjMat.dot(glScreenPosition)[:2]

    def mapWorldToScreen(self, coord):
        """Map a world co-ordinate to its corresponding QT screen co-ordinate.

        Args:
            coord (list[float, float]): The world co-ordinate to map from.
        Returns:
            list[float, float]: The mapped Qt screen co-ordinate.
        """
        worldCoord = np.array([coord[0], coord[1], 0.0, 1.0])
        screenGlCoord = self._projMat.dot(worldCoord)[:2]
        return self.mapGlToScreen(screenGlCoord)

    def zoom(self, coord, amount):
        """Zoom the projection matrix around a given world co-ordinate.

        Args:
            coord (list[float, float]): World space co-ordinate to zoom on.
            amount (float): Value to multiply the current scale by. Value of 1.0 is the same as no scale.
        """
        self.setProjectionMatrix(
            self.scaleMatrixAroundPoint(self._projMat, amount, amount, coord)
        )

    def resize(self, width, height):
        """Resize the camera output image.

        Args:
            width (int): New screen width.
            height (int): New screen height.
        """
        if self._initResizeFocusRegion is None:
            self._initResizeFocusRegion = self.getFocusRegion()
        [left, right, top, bottom] = self._initResizeFocusRegion

        self._screenWidth = float(width)
        self._screenHeight = float(height)
        self._screenAspectRatio = self._screenWidth / self._screenHeight

        halfHeight = float(top - bottom) / 2.0
        yMid = bottom + halfHeight
        scaledHalfHeight = halfHeight / self._screenAspectRatio
        bottom = yMid - scaledHalfHeight
        top = yMid + scaledHalfHeight

        self.focus(left, right, top, bottom, bufferScale=0.0, clearFocusCache=False)

    def setProjectionMatrix(self, matrix, clearFocusCache=True):
        """Set the projection matrix for the camera.

        Args:
            matrix (np.matrix(4x4)): The projection matrix to set.
            clearFocusCache (bool): If True, clear the cached focus region used during resize.
        """
        self._projMat = matrix
        self._invProjMat = np.linalg.inv(self._projMat)
        if clearFocusCache:
            self._initResizeFocusRegion = None

    def projectionMatrix(self):
        """The current projection matrix.

        Return:
            np.matrix(4x4): The current projection matrix.
        """
        return self._projMat

    def glProjectionMatrix(self):
        """Utility method to get the projection matrix in a way that can be used by GL.

        Return:
            float[16]: Flattened projection matrix.
        """
        return list(np.matrix.transpose(self.projectionMatrix()).flat)

    def scaleMatrixAroundPoint(
        self, matrix, xScale, yScale, coord, minScaleAmount=0.01
    ):
        """Scale a matrix around a given co-ordinate taking the current screen aspect ratio into account.

        Args:
            matrix (np.matrix(4x4)): The matrix to scale.
            xScale (float): The scale amount for the x axis.
            yScale (float): The scale amount for the y axis.
            coord (list[float, float]): The co-ordinate to scale the matrix around.
            minScaleAmount (float): The minimum scale allowed to help prevent flipping.
        """
        currentXScale = float(matrix[0][0])
        currentYScale = float(matrix[1][1])
        if (
            (xScale == 1.0 and yScale == 1.0)
            or currentXScale <= minScaleAmount
            or currentYScale <= minScaleAmount
        ):
            return matrix

        resultingXScale = currentXScale * float(xScale)
        resultingYScale = currentYScale * float(yScale)
        if resultingXScale <= minScaleAmount or resultingYScale <= minScaleAmount:
            resultingXScale = minScaleAmount
            resultingYScale = minScaleAmount * self._screenAspectRatio

        if coord[0] == 0.0 and coord[1] == 0.0:
            matrix[0][0] = resultingXScale
            matrix[1][1] = resultingYScale
        else:
            translationMatrix = self.createTransformationMatrix(coord[0], coord[1])
            matrix = matrix.dot(translationMatrix)
            matrix[0][0] = resultingXScale
            matrix[1][1] = resultingYScale
            matrix = matrix.dot(np.linalg.inv(translationMatrix))

        return matrix

    @staticmethod
    def createProjectionMatrix(left, right, top, bottom):
        """Utility method to generate a projection matrix from given focus region.

        Args:
            left (float): The left unit in world space of the focus region.
            right (float): The right unit in world space of the focus region.
            top (float): The top unit in world space of the focus region.
            bottom (float): The bottom unit in world space of the focus region.
        """
        xScale = 2.0 / float(right - left)
        yScale = 2.0 / float(top - bottom)

        xTransform = -(float(right + left) / float(right - left))
        yTransform = -(float(top + bottom) / float(top - bottom))

        projectionMat = np.identity(4)
        projectionMat[0][0] = xScale
        projectionMat[1][1] = yScale
        projectionMat[0][3] = xTransform
        projectionMat[1][3] = yTransform

        return projectionMat

    @staticmethod
    def createTransformationMatrix(x, y):
        """Utility method to generate a 4x4 2D transformation matrix.

        Args:
            x (float): The transformation value on the x axis.
            y (float): The transformation value on the y axis.
        Return:
            np.matrix(4x4): Transformation matrix.
        """
        matrix = np.identity(4)
        matrix[0][3] = x
        matrix[1][3] = y
        return matrix
