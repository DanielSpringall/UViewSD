# Copyright 2021 by Daniel Springall.
# This file is part of UViewSD, and is released under the "MIT License Agreement".
# Please see the LICENSE file that should have been included as part of this package.
from uviewsd.gl import utils as ug_utils

from ctypes import c_void_p
from OpenGL import GL
import numpy as np

import logging

logger = logging.getLogger(__name__)


class EdgesShape:
    def __init__(self, positions, indices, identifier, width=1.0):
        """OpenGl class for drawing uv edges.

        Args:
            positions (list[tuple(int, int)]):
                A list of tuples corresponding to a positions x and y values.
            indices (list[tuple(int, int)]):
                A list of tuples corresponding to an edges start and end index . e.g. [(uvPos0, uvPos1), (uvPos1, uvPos2), ...]
                where each index maps back to the uv positions. So uvPos0 -> uvPos1 would make up an edge.
            width (float):
                The line width to set for the edges.
        """
        self._positions = np.array(positions, dtype=np.float32)
        self._indices = np.array(indices, dtype=np.uint32)
        self._numUVs = self._indices.flatten().size
        self._identifier = identifier
        self._lineWidth = width

        self._color = (1.0, 1.0, 1.0)
        self._vao = None
        self._bao = None
        self._bbox = None

    def identifier(self):
        return self._identifier

    def bbox(self):
        """Calculate the bounding box of the shape.

        Returns:
            ug_utils.AABBox: The bbox of the shape.
        """
        if self._bbox is None:
            if self._numUVs <= 1:
                return None

            edge = self._positions[self._indices[0]]
            bbox = ug_utils.AABBox(edge[0], edge[1])
            for i in range(1, int(self._numUVs / 2)):
                edge = self._positions[self._indices[i]]
                bbox.addPosition(edge[0])
                bbox.addPosition(edge[1])
            self._bbox = bbox

        return self._bbox

    def initializeGLData(self):
        self._vao = GL.glGenVertexArrays(1)
        [pbo, ebo] = GL.glGenBuffers(2)

        GL.glBindVertexArray(self._vao)
        # Positions
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, pbo)
        GL.glBufferData(
            GL.GL_ARRAY_BUFFER,
            self._positions.nbytes,
            self._positions,
            GL.GL_STATIC_DRAW,
        )
        # Indices
        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, ebo)
        GL.glBufferData(
            GL.GL_ELEMENT_ARRAY_BUFFER,
            self._indices.nbytes,
            self._indices.flatten(),
            GL.GL_STATIC_DRAW,
        )

        GL.glVertexAttribPointer(0, 2, GL.GL_FLOAT, GL.GL_FALSE, 0, c_void_p(0))
        GL.glEnableVertexAttribArray(0)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
        GL.glBindVertexArray(0)

    def draw(self, shader):
        """OpenGl draw call.

        Args:
            shader (uviewsd.shader): The shader to use for the draw call. Assumed to already be set as in use.
        """
        if not self._vao:
            self.initializeGLData()
        shader.setVec3f("color", self._color)
        GL.glLineWidth(self._lineWidth)
        GL.glBindVertexArray(self._vao)
        GL.glDrawElements(GL.GL_LINES, self._numUVs, GL.GL_UNSIGNED_INT, None)
        GL.glBindVertexArray(0)


class TextureShape:
    def __init__(self, shader, textureRepeat=False):
        """OpenGl class for drawing plane with a given texture.

        Args:
            shader (shader.TextureShader):
                The texture shader to use for the draw call.
            textureRepeat (bool):
                If True, draw the plane/texture on every 1 by 1 unit used by the Grid class.
                If False, the plane/texture will only be drawn on the (0, 0) to (1, 1) units.
        """
        self._shader = shader
        self._texturePath = shader.texturePath()
        self._textureRepeat = textureRepeat
        self._update = True

        self._positions = self._positionData()
        self._indices = np.array((0, 1, 2, 2, 3, 1), dtype=np.int32)
        self._numVerts = self._indices.size

        self._vao = None

    def _positionData(self):
        """Get the position data of the vertices used for the texture plane."""
        max = Grid.NUM_GRIDS_FROM_ORIGIN if self._textureRepeat else 1.0
        min = -max if self._textureRepeat else 0.0
        return np.array(
            ((min, min), (min, max), (max, min), (max, max)),
            dtype=np.float32,
        )

    def identifier(self):
        return self._shader.texturePath()

    def initializeGLData(self):
        self._vao = GL.glGenVertexArrays(1)
        [self._vbo, ebo] = GL.glGenBuffers(2)

        GL.glBindVertexArray(self._vao)
        # Positions
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._vbo)
        GL.glBufferData(
            GL.GL_ARRAY_BUFFER,
            self._positions.nbytes,
            self._positions,
            GL.GL_STATIC_DRAW,
        )
        # Indices
        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, ebo)
        GL.glBufferData(
            GL.GL_ELEMENT_ARRAY_BUFFER,
            self._indices.nbytes,
            self._indices.flatten(),
            GL.GL_STATIC_DRAW,
        )

        GL.glVertexAttribPointer(0, 2, GL.GL_FLOAT, GL.GL_FALSE, 0, c_void_p(0))
        GL.glEnableVertexAttribArray(0)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
        GL.glBindVertexArray(0)

        if self._texturePath is not None:
            self._shader.bindTexture(self._texturePath)

        self._update = False

    def updateGLData(self):
        """Update the texture used in the shader, and the plane size."""
        if (
            self._texturePath is not None
            and self._texturePath != self._shader.texturePath()
        ):
            self._shader.bindTexture(self._texturePath)

        if self._positions[0][0] != 0.0 or self._textureRepeat:
            self._positions = self._positionData()
            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._vbo)
            GL.glBufferData(
                GL.GL_ARRAY_BUFFER,
                self._positions.nbytes,
                self._positions,
                GL.GL_STATIC_DRAW,
            )
            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

        self._update = False

    def setTexturePath(self, path):
        """
        Set the file path to use for the texture being displayed,
        will be updated on the next draw call.

        Args:
            path (str):
                The file path for the texture image to use.
        """
        if path != self._shader.texturePath():
            self._texturePath = path
            self._update = True

    def setTextureRepeat(self, textureRepeat):
        """Set the repeat state of the texture, will be updated on the next draw call.

        textureRepeat (bool):
                If True, draw the plane/texture on every 1 by 1 unit used by the Grid class.
                If False, the plane/texture will only be drawn on the (0, 0) to (1, 1) units.
        """
        if textureRepeat != self._textureRepeat:
            self._textureRepeat = textureRepeat
            self._update = True

    def draw(self, projectionMatrix):
        """OpenGl draw call.

        Args:
            projectionMatrix (float[16]): Projection matrix to set the shader with.
        """
        if self._vao is None:
            self.initializeGLData()
        elif self._update:
            self.updateGLData()
        if not self._shader.valid():
            return

        self._shader.use()
        self._shader.setMatrix4f("viewMatrix", projectionMatrix)

        GL.glBindVertexArray(self._vao)
        GL.glDrawElements(GL.GL_TRIANGLES, self._numVerts, GL.GL_UNSIGNED_INT, None)
        GL.glBindVertexArray(0)


class Grid:
    NUM_GRIDS_FROM_ORIGIN = 5
    LINE_INTERVALS = 10  # Small line every 0.1 units
    TOTAL_LINES = NUM_GRIDS_FROM_ORIGIN * LINE_INTERVALS

    def __init__(self):
        """OpenGL class for drawing all the lines that make up the background grid for the uv viewer."""
        self._lineData = None

    def initializeGLData(self):
        """Initialize the GL data for the lines. """
        incrementalLines = []
        unitLines = []
        originLines = []

        maxVal = self.NUM_GRIDS_FROM_ORIGIN
        minVal = -self.NUM_GRIDS_FROM_ORIGIN
        for i in range((self.TOTAL_LINES) * 2 + 1):
            offset = i / float(self.LINE_INTERVALS)
            lineOffset = minVal + offset
            lineVerts = [
                minVal,
                lineOffset,  # x start
                maxVal,
                lineOffset,  # x end
                lineOffset,
                minVal,  # y start
                lineOffset,
                maxVal,  # y end
            ]
            if lineOffset == 0:
                originLines.extend(lineVerts)
            elif offset - int(offset) == 0:
                unitLines.extend(lineVerts)
            else:
                incrementalLines.extend(lineVerts)

        uLine = [0.0, 0.0, 0.5, 0.0]
        vLine = [0.0, 0.0, 0.0, 0.5]

        baseColor = (0.0, 0.0, 0.0)
        incrementalColor = (0.23, 0.23, 0.23)
        originColor = (0.0, 0.0, 1.0)
        uColor = (1.0, 0.0, 0.0)
        vColor = (1.0, 1.0, 0.0)

        self._lineData = [
            self._buildGLLines(
                np.array(incrementalLines, dtype=np.float32), color=incrementalColor
            ),
            self._buildGLLines(
                np.array(unitLines, dtype=np.float32), color=baseColor
            ),
            self._buildGLLines(
                np.array(originLines, dtype=np.float32), color=originColor
            ),
            self._buildGLLines(np.array(uLine, dtype=np.float32), color=uColor),
            self._buildGLLines(np.array(vLine, dtype=np.float32), color=vColor),
        ]

    def _buildGLLines(self, lineData, color):
        """Build a series of GL lines.

        Args:
            lineData (np.array): Array of vertex positions for lines.
            color (tuple(int, int, int)): Color made up of RGB values to draw the lines with.
        Returns:
            dict{vao: int, numVerts: int, color: tuple(int, int, int)}:
                OpenGL data used to draw the lines with.
        """
        vao = GL.glGenVertexArrays(1)
        pbo = GL.glGenBuffers(1)

        GL.glBindVertexArray(vao)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, pbo)

        GL.glEnableVertexAttribArray(0)
        GL.glVertexAttribPointer(0, 2, GL.GL_FLOAT, GL.GL_FALSE, 0, c_void_p(0))

        GL.glBufferData(
            GL.GL_ARRAY_BUFFER, lineData.nbytes, lineData, GL.GL_STATIC_DRAW
        )

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
        GL.glBindVertexArray(0)

        data = {"vao": vao, "numVerts": int(len(lineData) / 2), "color": color}
        return data

    def draw(self, shader):
        """OpenGl draw call.

        Args:
            shader (uviewsd.shader): The shader to use for the draw call. Assumed to already be set as in use.
        """
        if self._lineData is None:
            self.initializeGLData()

        GL.glLineWidth(1.0)

        previousColor = None
        for data in self._lineData:
            # Set color
            color = data["color"]
            if color != previousColor:
                shader.setVec3f("color", color)
                previousColor = color

            # Draw
            GL.glBindVertexArray(data["vao"])
            GL.glDrawArrays(GL.GL_LINES, 0, data["numVerts"])
            GL.glBindVertexArray(0)
