# Copyright 2021 by Daniel Springall.
# This file is part of UViewSD, and is released under the "MIT License Agreement".
# Please see the LICENSE file that should have been included as part of this package.
from ctypes import c_void_p
from OpenGL import GL
from numpy.core.fromnumeric import repeat
from pxr import UsdGeom, UsdShade, Sdf
import numpy as np

import os
import logging

logger = logging.getLogger(__name__)


# USD
class PrimDataExtractor:
    VALID_PRIMVAR_TYPE_NAME = ("texCoord2f[]", "float2[]")
    VALID_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".tiff", ".bmp")

    def __init__(self, prim):
        """Helper class for extracting uv data from a USDGeom mesh."""
        self._mesh = UsdGeom.Mesh(prim) if prim.IsValid() else None
        self._shader = None
        self._validUVNames = None

    def prim(self):
        return self._mesh.GetPrim()

    def isValid(self):
        """Test a given USDGeom mesh has the relveant data to extract uv's from.

        Returns:
            bool: True if the mesh has the relevant data to extract uv's for. False otherwise.
        """
        if not self._mesh:
            logger.debug("Invalid mesh for uv data. %s.", self._mesh)
            return False
        if not self._mesh.GetFaceVertexCountsAttr().HasValue():
            logger.debug(
                "Invalid mesh for uv data. %s. Missing face vertex count attribute.",
                self._mesh,
            )
            return False
        if not self._mesh.GetFaceVertexIndicesAttr().HasValue():
            logger.debug(
                "Invalid mesh for uv data. %s. Missing face vertex indices attribute.",
                self._mesh,
            )
            return False
        return True

    # UV
    def validUVNames(self):
        """Get a list of uv names that are valid on the mesh.

        Returns:
            list[str]: List of valid uv names.
        """
        if self._validUVNames is None:
            self._validUVNames = []
            if self.isValid():
                for primvar in self._mesh.GetPrimvars():
                    if primvar.GetTypeName() not in self.VALID_PRIMVAR_TYPE_NAME:
                        continue
                    self._validUVNames.append(primvar.GetPrimvarName())
        return self._validUVNames

    def isUVNameValid(self, uvName):
        return uvName in self.validUVNames()

    def uvData(self, uvName):
        """Extract the uv data of a specific name from the mesh.

        Args:
            uvName (str): The name of the uv prim to get the data for.
        Returns:
            list[tuple(int, int)]:
                A list of tuples corresponding to an edges start and end index . e.g. [(uvPos0, uvPos1), (uvPos1, uvPos2), ...]
                where each index maps back to the uv positions. So uvPos0 -> uvPos1 would make up an edge.
        """
        if not self.isUVNameValid(uvName):
            logger.debug(
                "%s not a valid uv name for %s. Valid names: %s.",
                uvName,
                self._mesh,
                self.validUVNames(),
            )
            return None, None

        primvar = self._mesh.GetPrimvar(uvName)
        interpolation = primvar.GetInterpolation()
        if interpolation == UsdGeom.Tokens.faceVarying:
            return self._getFaceVaryingUVs(primvar)
        elif interpolation == UsdGeom.Tokens.vertex:
            return self._getVertexVaryingUVs(primvar)

        logger.error("Invalid interpolation (%s) for uv data.", interpolation)
        return None, None

    def _getFaceVaryingUVs(self, primvar):
        """Extract the face varying uv data from a primvar.

        Args:
            primvar (Usd.Primvar): The primvar to extract the uv data from.
        Returns:
            list[tuple(int, int)]:
                A list of tuples corresponding to an edges start and end index . e.g. [(uvPos0, uvPos1), (uvPos1, uvPos2), ...]
                where each index maps back to the uv positions. So uvPos0 -> uvPos1 would make up an edge.
        """
        faceVertCountList = self._mesh.GetFaceVertexCountsAttr().Get()
        uvPositions = primvar.Get()
        uvIndices = primvar.GetIndices()
        edgeIndices = self._createUVEdges(faceVertCountList, [uvIndices])
        return [uvPositions, edgeIndices]

    def _getVertexVaryingUVs(self, primvar):
        """Extract the vertex varying uv data from a primvar.

        Args:
            primvar (Usd.Primvar): The primvar to extract the uv data from.
        Returns:
            list[tuple(int, int)]:
                A list of tuples corresponding to an edges start and end index . e.g. [(uvPos0, uvPos1), (uvPos1, uvPos2), ...]
                where each index maps back to the uv positions. So uvPos0 -> uvPos1 would make up an edge.
        """
        faceVertCountList = self._mesh.GetFaceVertexCountsAttr().Get()
        faceVertexIndices = self._mesh.GetFaceVertexIndicesAttr().Get()
        uvPositions = primvar.Get()
        uvIndices = primvar.GetIndices()
        uvIndexMaps = [faceVertexIndices]
        if uvIndices:
            uvIndexMaps.append(uvIndices)
        edgeIndices = self._createUVEdges(faceVertCountList, uvIndexMaps)
        return [uvPositions, edgeIndices]

    @staticmethod
    def _createUVEdges(faceVertCountList, indexMaps):
        """Generate the uv edge indices from a given list of uv indices.

        Args:
            faceVertCountList list[int]:
                List of number of indices per face.
            indexMaps list[list[]]:
                List of index maps to map a given face vert id back to it's corresponding uv index.
        Returns:
            list[tuple(int, int)]:
                A list of tuples corresponding to an edges start and end index . e.g. [(uvPos0, uvPos1), (uvPos1, uvPos2), ...]
                where each index maps back to the uv positions. So uvPos0 -> uvPos1 would make up an edge.
        """
        edgeIndices = []
        consumedIndices = 0
        for faceVertCount in faceVertCountList:
            for i in range(faceVertCount):
                firstIndex = consumedIndices + i
                secondIndex = (
                    consumedIndices if i == (faceVertCount - 1) else firstIndex + 1
                )
                for indexMap in indexMaps:
                    firstIndex = indexMap[firstIndex]
                    secondIndex = indexMap[secondIndex]
                edgeIndices.append((firstIndex, secondIndex))
            consumedIndices += faceVertCount
        return edgeIndices

    @staticmethod
    def edgeBoundariesFromEdgeIndices(uvIndices):
        """Get the indices that make up the uv boundary edges.

        Args:
            uvIndices list[tuple(int, int)]:
                A list of tuples corresponding to an edges start and end index . e.g. [(uvPos0, uvPos1), (uvPos1, uvPos2), ...]
                where each index maps back to the uv positions. So uvPos0 -> uvPos1 would make up an edge.
        Returns:
            list[tuple(int, int)]:
                A list of tuples corresponding to start/end uv positions of boundary uv edges.
        """
        edgeCountMap = {}
        for uvEdge in uvIndices:
            edge = Edge(uvEdge[0], uvEdge[1])
            if edge in edgeCountMap:
                edgeCountMap[edge] += 1
            else:
                edgeCountMap[edge] = 1

        boundaryEdges = []
        for edge, count in edgeCountMap.items():
            if count == 1:
                boundaryEdges.append((edge.startIndex, edge.endIndex))
        return boundaryEdges

    # TEXTURE
    def textureData(self):
        """
        Get any texture file paths used as inputs to the surface shader
        on the meshes bound material.

        Returns:
            list[str]: A unique list of texture file absolute paths.
        """
        shader = self.meshShader()
        if shader is None:
            return []

        paths = []
        for path in self._getTexturesFromShader(shader):
            if path not in paths:
                paths.append(path)

        return paths

    def meshShader(self):
        """Get the shader used on the mesh if one exists.

        Returns:
            UsdShade.Shader | None: The shader if one exists, otherwise None.
        """
        if self._shader is None:
            prim = self.prim()
            binding = UsdShade.MaterialBindingAPI(prim)
            (material, _) = binding.ComputeBoundMaterial()
            if material:
                (shader, _, __) = material.ComputeSurfaceSource()
                if shader:
                    self._shader = shader
                else:
                    logger.debug("No surface shader for %s", prim)
            else:
                logger.debug("No material bound to %s", prim)
        return self._shader

    @classmethod
    def _getUpStreamInputs(cls, input, inputsVisited):
        """Recursively search upstream for all possible inputs.
        Args:
            input(UsdShade.Input):
                The input to start the search from.
            inputsVisited(list[UsdShade.Input]):
                List of previously visited input nodes to compare against to ensure no
                search recursion occurs. New inputs discovered will be added to this list.
        """
        for connection in input.GetConnectedSources():
            if not connection:
                continue
            for input in connection[0].source.GetInputs():
                if input in inputsVisited:
                    continue
                inputsVisited.append(input)
                cls._getUpStreamInputs(input, inputsVisited)

    @classmethod
    def _getTexturesFromShader(cls, shader):
        """Extract all texture file paths used in a shader.

        Returns:
            list[str]: A unique list of texture file paths.
        """
        inputs = []
        for input in shader.GetInputs():
            inputs.append(input)
            cls._getUpStreamInputs(input, inputs)

        paths = []
        for input in inputs:
            attribute = input.GetAttr().Get()
            if not isinstance(attribute, Sdf.AssetPath):
                continue
            path = attribute.resolvedPath
            if (
                os.path.isfile(path)
                and os.path.splitext(path)[-1] in cls.VALID_IMAGE_EXTENSIONS
            ):
                paths.append(path)
        return paths


# OPENGL
class UVShape:
    def __init__(self, positions, indices, identifier):
        """OpenGl class for drawing uv edges.

        Args:
            positions (list[float]):
                A flat list of uv positions. e.g. [uvPos0.u, uvPos0.v, uvPos1.u, uvPose1.v, ...]
            indices (list[tuple(int, int)]):
                A list of tuples corresponding to an edges start and end index . e.g. [(uvPos0, uvPos1), (uvPos1, uvPos2), ...]
                where each index maps back to the uv positions. So uvPos0 -> uvPos1 would make up an edge.
        """
        self._positions = np.array(positions, dtype=np.float32)
        self._indices = np.array(indices, dtype=np.int)
        self._numUVs = self._indices.flatten().size
        self._identifier = identifier
        self._boundaryIndices = None
        self._numBoundaryUVs = None

        self._color = (1.0, 1.0, 1.0)
        self._vao = None
        self._bao = None
        self._bbox = None

    def identifier(self):
        return self._identifier

    def bbox(self):
        """Calculate the bounding box from the uv positions.

        Returns:
            BBox: The bbox surounding the uv positions.
        """
        if self._bbox is None:
            if self._numUVs <= 1:
                return None

            edge = self._positions[self._indices[0]]
            bbox = BBox(edge[0], edge[1])
            for i in range(1, int(self._numUVs / 2)):
                edge = self._positions[self._indices[i]]
                bbox.updateWithPosition(edge[0])
                bbox.updateWithPosition(edge[1])
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

    def initializeBoundaryGLData(self):
        self._boundaryIndices = np.array(
            PrimDataExtractor.edgeBoundariesFromEdgeIndices(self._indices),
            dtype=np.int,
        )
        self._numBoundaryUVs = self._boundaryIndices.flatten().size

        self._bao = GL.glGenVertexArrays(1)
        [pbo, ebo] = GL.glGenBuffers(2)

        GL.glBindVertexArray(self._bao)
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
            self._boundaryIndices.nbytes,
            self._boundaryIndices.flatten(),
            GL.GL_STATIC_DRAW,
        )

        GL.glVertexAttribPointer(0, 2, GL.GL_FLOAT, GL.GL_FALSE, 0, c_void_p(0))
        GL.glEnableVertexAttribArray(0)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
        GL.glBindVertexArray(0)

    def draw(self, shader, drawBoundaries=False):
        """OpenGl draw call.

        Args:
            shader (uviewsd.shader): The shader to use for the draw call. Assumed to already be set as in use.
            drawBoundaries (bool): If true, draw the uv edge boundary highlights.
        """
        if not self._vao:
            self.initializeGLData()
        if drawBoundaries and not self._bao:
            self.initializeBoundaryGLData()

        shader.setVec3f("color", self._color)

        GL.glLineWidth(1.0)
        GL.glBindVertexArray(self._vao)
        GL.glDrawElements(GL.GL_LINES, self._numUVs, GL.GL_UNSIGNED_INT, None)

        if drawBoundaries:
            GL.glLineWidth(3.0)
            GL.glBindVertexArray(self._bao)
            GL.glDrawElements(
                GL.GL_LINES, self._numBoundaryUVs, GL.GL_UNSIGNED_INT, None
            )

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
            GL.glBindVertexArray(self._vao)
            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._vbo)
            GL.glBufferData(
                GL.GL_ARRAY_BUFFER,
                self._positions.nbytes,
                self._positions,
                GL.GL_STATIC_DRAW,
            )

        self._update = False

    def setTexturePath(self, path):
        if path != self._shader.texturePath():
            self._texturePath = path
            self._update = True

    def setTextureRepeat(self, textureRepeat):
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
        if self._update:
            self.updateGLData()
        if not self._shader.valid():
            return

        self._shader.use()
        self._shader.setMatrix4f("viewMatrix", projectionMatrix)

        if not self._vao:
            self.initializeGLData()

        GL.glBindVertexArray(self._vao)
        GL.glDrawElements(GL.GL_TRIANGLES, self._numVerts, GL.GL_UNSIGNED_INT, None)

        GL.glBindVertexArray(0)


class Grid:
    NUM_GRIDS_FROM_ORIGIN = 5
    LINE_INTERVALS = 10  # Small line every 0.1 units
    TOTAL_LINES = NUM_GRIDS_FROM_ORIGIN * LINE_INTERVALS

    def __init__(self):
        """OpenGL class for drawing all the lines that make up the background grid for the uv viewer."""
        incrementalLines = []
        unitLines = []
        originLines = []

        maxVal = self.NUM_GRIDS_FROM_ORIGIN
        minVal = -self.NUM_GRIDS_FROM_ORIGIN
        for i in range((self.TOTAL_LINES) * 2 + 1):
            offset = i / self.LINE_INTERVALS
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
            self.initializeGLData(
                np.array(incrementalLines, dtype=np.float32), color=incrementalColor
            ),
            self.initializeGLData(
                np.array(unitLines, dtype=np.float32), color=baseColor
            ),
            self.initializeGLData(
                np.array(originLines, dtype=np.float32), color=originColor
            ),
            self.initializeGLData(np.array(uLine, dtype=np.float32), color=uColor),
            self.initializeGLData(np.array(vLine, dtype=np.float32), color=vColor),
        ]

    def initializeGLData(self, lineData, color):
        """Initialize the OpenGL data for a given set of line data.

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


# UTILITIES
class BBox:
    def __init__(self, pos0, pos1):
        if pos0[0] <= pos1[0]:
            self.xMin = pos0[0]
            self.xMax = pos1[0]
        else:
            self.xMin = pos1[0]
            self.xMax = pos0[0]
        if pos0[1] <= pos1[1]:
            self.yMin = pos0[1]
            self.yMax = pos1[1]
        else:
            self.yMin = pos1[1]
            self.yMax = pos0[1]

    def updateWithPosition(self, pos):
        if self.xMin > pos[0]:
            self.xMin = pos[0]
        elif self.xMax < pos[0]:
            self.xMax = pos[0]
        if self.yMin > pos[1]:
            self.yMin = pos[1]
        elif self.yMax < pos[1]:
            self.yMax = pos[1]

    def updateWithBBox(self, otherBBox):
        if self.xMin > otherBBox._xMin:
            self.xMin = otherBBox._xMin
        if self.xMax < otherBBox._xMax:
            self.xMax = otherBBox._xMax
        if self.yMin > otherBBox._yMin:
            self.yMin = otherBBox._yMin
        if self.yMax > otherBBox._yMax:

            self.yMax = otherBBox._yMax


class Edge:
    def __init__(self, startIndex, endIndex):
        self.startIndex = min(startIndex, endIndex)
        self.endIndex = max(startIndex, endIndex)

    def __hash__(self):
        return hash((self.startIndex, self.endIndex))

    def __eq__(self, otherEdge):
        return (
            self.startIndex == otherEdge.startIndex
            and self.endIndex == otherEdge.endIndex
        )
