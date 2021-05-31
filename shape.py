from ctypes import c_void_p
from OpenGL import GL
import numpy as np
from pxr import UsdGeom

import shader

import logging
logger = logging.getLogger(__name__)


class UVShape:
    def __init__(self, lines):
        self.bound = False
        self._vao = None
        self._colour = (1.0, 1.0, 1.0)
        self._shader = None
        self._lines = np.array(lines, dtype=np.float32)
        self._numLines = int(len(self._lines) / 2)

    def initializeGLData(self):
        self._shader = shader.ShaderProgram(vertexShaderName="line", fragmentShaderName="line")
        self._vao = GL.glGenVertexArrays(1)
        pbo = GL.glGenBuffers(1)

        GL.glBindVertexArray(self._vao)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, pbo)

        GL.glEnableVertexAttribArray(0)
        GL.glVertexAttribPointer(0, 2, GL.GL_FLOAT, GL.GL_FALSE, 0, c_void_p(0))

        GL.glBufferData(GL.GL_ARRAY_BUFFER, self._lines.nbytes, self._lines, GL.GL_STATIC_DRAW)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
        GL.glBindVertexArray(0)
        self.bound = True

    def draw(self, projectionMatrix):
        if not self.bound:
            self.initializeGLData()

        self._shader.use()
        self._shader.setMatrix4f("viewMatrix", projectionMatrix)

        GL.glLineWidth(1.0)
        GL.glBindVertexArray(self._vao)
        self._shader.setVec3f("colour", self._colour)
        GL.glDrawArrays(GL.GL_LINES, 0, self._numLines)
        GL.glBindVertexArray(0)


class MeshUVs:
    def __init__(self, mesh):
        self._mesh = mesh
        self._validUVNames = None

    def prim(self):
        return self._mesh.GetPrim()

    @staticmethod
    def validMesh(mesh):
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
        validUVNames = []
        for primvar in mesh.GetPrimvars():
            if primvar.GetTypeName() not in ["texCoord2f[]", "float2[]"]:
                continue
            validUVNames.append(primvar.GetPrimvarName())
        return validUVNames

    def validUVNames(self):
        if self._validUVNames is None:
            self._validUVNames = self._getValidUVNames(self._mesh)
        return self._validUVNames

    def isUVNameValid(self, uvName):
        return uvName in self.validUVNames()

    def uvData(self, uvName):
        if not self.isUVNameValid(uvName):
            logger.debug("%s not a valid uv name for %s. Valid names: %s.", uvName, self._mesh, self.validUVNames())
            return [None, None]

        primvar = self._mesh.GetPrimvar(uvName)
        interpolation = primvar.GetInterpolation()
        if interpolation == UsdGeom.Tokens.faceVarying:
            return self._getFaceVaryingUVs(primvar)
        elif interpolation == UsdGeom.Tokens.vertex:
            return self._getVertexVaryingUVs(primvar)

        logger.error("Invalid interpolation (%s) for uv data.", interpolation)
        return [None, None]

    def _getFaceVaryingUVs(self, primvar):
        faceVertCountList = self._mesh.GetFaceVertexCountsAttr().Get()
        uvPositions = primvar.Get()
        uvIndices = primvar.GetIndices()
        edgeIndices = self._createUVEdges(faceVertCountList, [uvIndices])
        return [uvPositions, edgeIndices]

    def _getVertexVaryingUVs(self, primvar):
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


NUM_GRIDS_FROM_ORIGIN = 5
LINE_INTERVALS = 10 # Line every 0.1 units
TOTAL_LINES = NUM_GRIDS_FROM_ORIGIN * LINE_INTERVALS

class Grid:
    def __init__(self):
        self._shader = shader.ShaderProgram(vertexShaderName="line", fragmentShaderName="line")

        incrementalLines = []
        unitLines = []
        originLines = []

        maxVal = NUM_GRIDS_FROM_ORIGIN
        minVal = -NUM_GRIDS_FROM_ORIGIN
        for i in range((TOTAL_LINES) * 2 + 1):
            offset = i / LINE_INTERVALS
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

        baseColour = (0.0, 0.0, 0.0)
        incrementalColour = (0.23, 0.23, 0.23)
        originColour = (0.0, 0.0, 1.0)
        uColour = (1.0, 0.0, 0.0)
        vColor = (1.0, 1.0, 0.0)
        self._lineData = [
            self.initializeGLData(np.array(incrementalLines, dtype=np.float32), colour=incrementalColour),
            self.initializeGLData(np.array(unitLines, dtype=np.float32), colour=baseColour),
            self.initializeGLData(np.array(originLines, dtype=np.float32), colour=originColour),
            self.initializeGLData(np.array(uLine, dtype=np.float32), colour=uColour),
            self.initializeGLData(np.array(vLine, dtype=np.float32), colour=vColor),
        ]

    def initializeGLData(self, lineData, colour):
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
            "colour": colour
        }
        return data

    def draw(self, projectionMatrix):
        self._shader.use()
        self._shader.setMatrix4f("viewMatrix", projectionMatrix)

        GL.glLineWidth(1.0)
        for data in self._lineData:
            GL.glBindVertexArray(data["vao"])
            self._shader.setVec3f("colour", data["colour"])
            GL.glDrawArrays(GL.GL_LINES, 0, data["numVerts"])
            GL.glBindVertexArray(0)
