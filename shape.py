from ctypes import c_void_p
from OpenGL import GL
import numpy as np

import shader


class BaseShape:
    def __init__(self):
        self._positions = None
        self._indices = None
        self._numVertices = None

        self._shader = None

        self._vao = None
        self._pbo = None
        self._uvbo = None

    def initializeGLData(self):
        self._vao = GL.glGenVertexArrays(1)
        [self._pbo, self._uvbo, ebo] = GL.glGenBuffers(3)

        GL.glBindVertexArray(self._vao)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._pbo)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, self._positions.nbytes, self._positions, GL.GL_STATIC_DRAW)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._uvbo)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, self._uvs.nbytes, self._uvs, GL.GL_STATIC_DRAW)

        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, ebo)
        GL.glBufferData(GL.GL_ELEMENT_ARRAY_BUFFER, self._indices.nbytes, self._indices, GL.GL_STATIC_DRAW)

        GL.glEnableVertexAttribArray(0)
        GL.glVertexAttribPointer(0, 2, GL.GL_FLOAT, GL.GL_FALSE, 0, c_void_p(0))
        GL.glEnableVertexAttribArray(1)
        GL.glVertexAttribPointer(1, 2, GL.GL_FLOAT, GL.GL_FALSE, 0, c_void_p(0))

        GL.glBindVertexArray(0); 

    def draw(self, projectionMatrix):
        self._shader.use()
        self._shader.setMatrix4f("viewMatrix", projectionMatrix)

        GL.glBindVertexArray(self._vao)
        GL.glDrawElements(GL.GL_TRIANGLES, self._numVertices, GL.GL_UNSIGNED_INT, c_void_p(0))
        GL.glBindVertexArray(0)


class UVShape:
    def __init__(self, lines):
        BaseShape.__init__(self)

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


NUM_GRIDS_FROM_ORIGIN = 5
LINE_INTERVALS = 10 # Line every 0.1 units
TOTAL_LINES = NUM_GRIDS_FROM_ORIGIN * LINE_INTERVALS

class Grid:
    def __init__(self):
        BaseShape.__init__(self)

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
