from ctypes import c_void_p
from OpenGL import GL
import numpy as np
from pxr import UsdGeom

import shader

import logging
logger = logging.getLogger(__name__)


# USD
class MeshUVs:
    def __init__(self, mesh):
        """ Helper class for extracting uv data from a USDGeom mesh. """
        self._mesh = mesh
        self._validUVNames = None

    def prim(self):
        return self._mesh.GetPrim()

    @staticmethod
    def validMesh(mesh):
        """ Test a given USDGeom mesh has the relveant data to extract uv's from.
        
        Returns:
            bool: True if the mesh has the relevant data to extract uv's for. False otherwise.
        """
        if not mesh:
            logger.debug("Invalid mesh for uv data. %s.", mesh)
            return False
        if not mesh.GetFaceVertexCountsAttr():
            logger.debug("Invalid mesh for uv data. %s. Missing face vertex count attribute.", mesh)
            return False
        if not mesh.GetFaceVertexIndicesAttr():
            logger.debug("Invalid mesh for uv data. %s. Missing face vertex indices attribute.", mesh)
            return False
        return True

    @staticmethod
    def _getValidUVNames(mesh):
        """ Return a list of all the uv names from the prim vars on the mesh.
        
        Returns:
            list[str]: List of valid uv names.
        """
        validUVNames = []
        for primvar in mesh.GetPrimvars():
            if primvar.GetTypeName() not in ["texCoord2f[]", "float2[]"]:
                continue
            validUVNames.append(primvar.GetPrimvarName())
        return validUVNames

    def validUVNames(self):
        """ Get a list of uv names that are valid on the mesh.
        
        Returns:
            list[str]: List of valid uv names.
        """
        if self._validUVNames is None:
            self._validUVNames = self._getValidUVNames(self._mesh)
        return self._validUVNames

    def isUVNameValid(self, uvName):
        return uvName in self.validUVNames()

    def uvData(self, uvName):
        """ Extract the uv data of a specific name from the mesh.
        
        Args:
            uvName (str): The name of the uv prim to get the data for.
        Returns:
            list[floats] | None, list[tuple(int, int)] | None:
                A list of uv positions, and a list of tuples for each edges uv indices.
        """
        if not self.isUVNameValid(uvName):
            logger.debug("%s not a valid uv name for %s. Valid names: %s.", uvName, self._mesh, self.validUVNames())
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
        """ Extract the face varying uv data from a primvar.

        Args:
            primvar (Usd.Primvar): The primvar to extract the uv data from.
        Returns:
            list[floats] | None, list[tuple(int, int)] | None:
                A list of uv positions, and a list of tuples for each edges uv indices.
        """
        faceVertCountList = self._mesh.GetFaceVertexCountsAttr().Get()
        uvPositions = primvar.Get()
        uvIndices = primvar.GetIndices()
        edgeIndices = self._createUVEdges(faceVertCountList, [uvIndices])
        return [uvPositions, edgeIndices]

    def _getVertexVaryingUVs(self, primvar):
        """ Extract the vertex varying uv data from a primvar.

        Args:
            primvar (Usd.Primvar): The primvar to extract the uv data from.
        Returns:
            list[floats] | None, list[tuple(int, int)] | None:
                A list of uv positions, and a list of tuples for each edges uv indices.
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
        """ Generate the uv edge indices from a given list of uv indices.

        Args:
            faceVertCountList list[int]:
                List of number of indices per face.
            indexMaps list[list[]]:
                List of index maps to map a given face vert id back to it's corresponding uv index.
        """
        edges = []
        consumedIndices = 0
        for faceVertCount in faceVertCountList:
            for i in range(faceVertCount):
                firstIndex = consumedIndices + i
                secondIndex = consumedIndices if i  == (faceVertCount - 1) else firstIndex + 1
                for indexMap in indexMaps:
                    firstIndex = indexMap[firstIndex]
                    secondIndex = indexMap[secondIndex]
                edges.append((firstIndex, secondIndex))
            consumedIndices += faceVertCount
        return edges


# OPENGL
class UVShape:
    def __init__(self, edges):
        """ OpenGl class for drawing uv edges.
        
        Args:
            edges (list[float]):
                A list of uv positions. Every 2 items in the list corresponds to a start and end point of a line.
        """
        self.bound = False
        self._vao = None
        self._color = (1.0, 1.0, 1.0)
        self._shader = None
        self._edges = np.array(edges, dtype=np.float32)
        self._numEdges = int(len(self._edges) / 2)

    def initializeGLData(self):
        """ Initialize the OpenGL data for drawing. Should only be called once. """
        self._shader = shader.ShaderProgram(vertexShaderName="line", fragmentShaderName="line")
        self._vao = GL.glGenVertexArrays(1)
        pbo = GL.glGenBuffers(1)

        GL.glBindVertexArray(self._vao)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, pbo)

        GL.glEnableVertexAttribArray(0)
        GL.glVertexAttribPointer(0, 2, GL.GL_FLOAT, GL.GL_FALSE, 0, c_void_p(0))

        GL.glBufferData(GL.GL_ARRAY_BUFFER, self._edges.nbytes, self._edges, GL.GL_STATIC_DRAW)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
        GL.glBindVertexArray(0)
        self.bound = True

    def draw(self, projectionMatrix):
        """ OpenGl draw call.

        Args:
            projectionMatrix (float[16]): The projection matrix to pass the shader.
        """
        if not self.bound:
            self.initializeGLData()

        self._shader.use()
        self._shader.setMatrix4f("viewMatrix", projectionMatrix)

        GL.glLineWidth(1.0)
        GL.glBindVertexArray(self._vao)
        self._shader.setVec3f("color", self._color)
        GL.glDrawArrays(GL.GL_LINES, 0, self._numEdges)
        GL.glBindVertexArray(0)


class Grid:
    NUM_GRIDS_FROM_ORIGIN = 5
    LINE_INTERVALS = 10 # Small line every 0.1 units
    TOTAL_LINES = NUM_GRIDS_FROM_ORIGIN * LINE_INTERVALS

    def __init__(self):
        """ OpenGL class for drawin the all the lines that make up the background grid for the uv viewer. """
        self._shader = shader.ShaderProgram(vertexShaderName="line", fragmentShaderName="line")

        incrementalLines = []
        unitLines = []
        originLines = []

        maxVal = self.NUM_GRIDS_FROM_ORIGIN
        minVal = -self.NUM_GRIDS_FROM_ORIGIN
        for i in range((self.TOTAL_LINES) * 2 + 1):
            offset = i / self.LINE_INTERVALS
            lineOffset = minVal + offset
            lineVerts = [
                minVal, lineOffset, # x start
                maxVal, lineOffset, # x end
                lineOffset, minVal, # y start
                lineOffset, maxVal, # y end
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
            self.initializeGLData(np.array(incrementalLines, dtype=np.float32), color=incrementalColor),
            self.initializeGLData(np.array(unitLines, dtype=np.float32), color=baseColor),
            self.initializeGLData(np.array(originLines, dtype=np.float32), color=originColor),
            self.initializeGLData(np.array(uLine, dtype=np.float32), color=uColor),
            self.initializeGLData(np.array(vLine, dtype=np.float32), color=vColor),
        ]

    def initializeGLData(self, lineData, color):
        """ Initialize the OpenGL data for a given set of line data.

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

        GL.glBufferData(GL.GL_ARRAY_BUFFER, lineData.nbytes, lineData, GL.GL_STATIC_DRAW)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
        GL.glBindVertexArray(0)

        data = {
            "vao": vao,
            "numVerts": int(len(lineData) / 2),
            "color": color
        }
        return data

    def draw(self, projectionMatrix):
        """ OpenGl draw call.

        Args:
            projectionMatrix (float[16]): The projection matrix to pass the shader.
        """
        self._shader.use()
        self._shader.setMatrix4f("viewMatrix", projectionMatrix)

        GL.glLineWidth(1.0)
        for data in self._lineData:
            GL.glBindVertexArray(data["vao"])
            self._shader.setVec3f("color", data["color"])
            GL.glDrawArrays(GL.GL_LINES, 0, data["numVerts"])
            GL.glBindVertexArray(0)
