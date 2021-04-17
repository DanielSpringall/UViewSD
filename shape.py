from ctypes import c_void_p
from shader import ShaderProgram
from OpenGL import GL
import numpy as np


class BaseShape:
    def __init__(self):
        self._positions = None
        self._indices = None
        self._numVertices = None

        self._shader = None

        self._vao = None
        self._pbo = None
        self._uvbo = None

    def setupMesh(self):
        self._vao = GL.glGenVertexArrays(1)
        [self._pbo, self._uvbo, ebo] = GL.glGenBuffers(3)

        GL.glBindVertexArray(self._vao)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._pbo)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, self._positions.nbytes, self._positions, GL.GL_STATIC_DRAW)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._uvbo)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, self._uvs.nbytes, self._uvs, GL.GL_STATIC_DRAW)

        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, ebo)
        GL.glBufferData(GL.GL_ELEMENT_ARRAY_BUFFER, self._indices.nbytes, self._indices, GL.GL_STATIC_DRAW)

        GL.glBindVertexArray(0); 

    def _setupShader(self, camera):
        self._shader.use()
        self._shader.setMatrix4f("viewMatrix", camera.projectionMatrix())

    def draw(self, camera):
        self._setupShader(camera)

        GL.glBindVertexArray(self._vao)
        GL.glEnableVertexAttribArray(0)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._pbo)
        GL.glVertexAttribPointer(0, 2, GL.GL_FLOAT, GL.GL_FALSE, 0, c_void_p(0))
        GL.glEnableVertexAttribArray(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._uvbo)
        GL.glVertexAttribPointer(1, 2, GL.GL_FLOAT, GL.GL_FALSE, 0, c_void_p(0))

        GL.glDrawElements(GL.GL_TRIANGLES, self._numVertices, GL.GL_UNSIGNED_INT, c_void_p(0))

        GL.glDisableVertexAttribArray(0)
        GL.glDisableVertexAttribArray(2)


class GridOld(BaseShape):
    def __init__(self):
        BaseShape.__init__(self)

        self._shader = ShaderProgram(vertexShaderName="default2", fragmentShaderName="grid")
        self._positions = np.array(
            [-10.0, -10.0,
             -10.0,  10.0,
              10.0, -10.0,
              10.0,  10.0], dtype=np.float32
        )
        self._indices = np.array(
            [0, 1, 2,
             1, 2, 3], dtype=np.int
        )
        self._uvs = np.array(
            [0.0, 0.0,
             0.0, 1.0,
             1.0, 0.0,
             1.0, 1.0], dtype=np.float32
        )
        self._numVertices = len(self._indices)
        self.setupMesh()

    def _setupShader(self, camera):
        BaseShape._setupShader(self, camera)
        self._shader.setFloat("imageWidth", float(camera._width))
        self._shader.setFloat("imageHeight", float(camera._height))




class Grid(BaseShape):
    def __init__(self):
        BaseShape.__init__(self)

        self._shader = ShaderProgram()

        numGridsFromOrigin = 1 # Number of 1 by 1 grids to draw
        lineIntervals = 10 # Small lines within each 1 by 1 grid

        smallLines = [] # Fractions
        largeLines = [] # Whole numbers
        maxVal = numGridsFromOrigin
        minVal = -numGridsFromOrigin
        for i in range((numGridsFromOrigin * lineIntervals) * 2 + 1):
            offset = i / lineIntervals
            lineOffset = minVal + offset
            lineVerts = [
                minVal, lineOffset, # x start
                maxVal, lineOffset, # x end
                lineOffset, minVal, # y start
                lineOffset, maxVal, # y end
            ]
            if offset - int(offset) == 0:
                largeLines.extend(lineVerts)
            else:
                smallLines.extend(lineVerts)

        self._lineData = [
            self.initializeGLData(np.array(largeLines, dtype=np.float32), width=3.0, colour=(0.2, 0.2, 0.2)),
            self.initializeGLData(np.array(smallLines, dtype=np.float32), width=1.0, colour=(0.2, 0.2, 0.2)),
        ]

    @staticmethod
    def initializeGLData(lineData, width, colour):
        data = {}
        data["vao"] = GL.glGenVertexArrays(1)
        data["pbo"] = GL.glGenBuffers(1)
        data["numVerts"] = int(len(lineData) / 2)
        data["width"] = width
        data["colour"] = colour

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, data["pbo"])
        GL.glBufferData(GL.GL_ARRAY_BUFFER, lineData.nbytes, lineData, GL.GL_STATIC_DRAW)

        GL.glBindVertexArray(0)
        return data

    def draw(self, camera):
        self._setupShader(camera)

        for data in self._lineData:
            GL.glBindVertexArray(data["vao"])
            GL.glVertexAttribPointer(0, 2, GL.GL_FLOAT, GL.GL_FALSE, 0, c_void_p(0))
            GL.glEnableVertexAttribArray(0)

            GL.glLineWidth(data["width"])
            GL.glDrawArrays(GL.GL_LINES, 0, data["numVerts"])

            GL.glDisableVertexAttribArray(0)
            GL.glBindVertexArray(0)


    def _setupShader(self, camera):
        BaseShape._setupShader(self, camera)
