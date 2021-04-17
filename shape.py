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

    def _setupShader(self, camera):
        self._shader.use()
        self._shader.setMatrix4f("viewMatrix", camera.projectionMatrix())

    def draw(self, camera):
        self._setupShader(camera)
        GL.glBindVertexArray(self._vao)
        GL.glDrawElements(GL.GL_TRIANGLES, self._numVertices, GL.GL_UNSIGNED_INT, c_void_p(0))
        GL.glBindVertexArray(0)


class TestShape(BaseShape):
    def __init__(self):
        BaseShape.__init__(self)

        self._shader = ShaderProgram()
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
        self.initializeGLData()

    def _setupShader(self, camera):
        BaseShape._setupShader(self, camera)
        self._shader.setFloat("imageWidth", float(camera._width))
        self._shader.setFloat("imageHeight", float(camera._height))


class Grid:
    def __init__(self):
        BaseShape.__init__(self)

        self._shader = ShaderProgram(vertexShaderName="line", fragmentShaderName="line")

        numGridsFromOrigin = 5
        lineIntervals = 10 # Line every 0.1 units

        incrementalLines = []
        singleUnitLines = []
        originLines = []

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
            if lineOffset == 0:
                originLines.extend(lineVerts)
            elif offset - int(offset) == 0:
                singleUnitLines.extend(lineVerts)
            else:
                incrementalLines.extend(lineVerts)

        uLine = [0.0, 0.0, 0.5, 0.0]
        vLine = [0.0, 0.0, 0.0, 0.5]

        baseColour = (0.2, 0.2, 0.2)
        originColour = (0.1, 0.1, 0.95)
        uColour = (1.0, 0.0, 0.0)
        vColor = (1.0, 1.0, 0.0)
        self._lineData = [
            self.initializeGLData(np.array(singleUnitLines, dtype=np.float32), width=2.0, colour=baseColour),
            self.initializeGLData(np.array(incrementalLines, dtype=np.float32), width=1.0, colour=baseColour),
            self.initializeGLData(np.array(originLines, dtype=np.float32), width=2.0, colour=originColour),
            self.initializeGLData(np.array(originLines, dtype=np.float32), width=2.0, colour=originColour),
            self.initializeGLData(np.array(uLine, dtype=np.float32), width=2.0, colour=uColour),
            self.initializeGLData(np.array(vLine, dtype=np.float32), width=2.0, colour=vColor),
        ]

    def initializeGLData(self, lineData, width, colour):
        vao = GL.glGenVertexArrays(1)
        pbo = GL.glGenBuffers(1)

        GL.glBindVertexArray(vao)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, pbo)

        GL.glEnableVertexAttribArray(0)
        GL.glVertexAttribPointer(0, 2, GL.GL_FLOAT, GL.GL_FALSE, 0, c_void_p(0))

        GL.glBufferData(GL.GL_ARRAY_BUFFER, lineData.nbytes, lineData, GL.GL_STATIC_DRAW)

        GL.glBindVertexArray(0)

        data = {
            "vao": vao,
            "numVerts": int(len(lineData) / 2),
            "width": width,
            "colour": colour
        }
        return data

    def draw(self, camera):
        self._setupShader(camera)

        for data in self._lineData:
            GL.glBindVertexArray(data["vao"])
            self._shader.setVec3f("colour", data["colour"])
            GL.glLineWidth(data["width"])
            GL.glDrawArrays(GL.GL_LINES, 0, data["numVerts"])
            GL.glBindVertexArray(0)

    def _setupShader(self, camera):
        self._shader.use()
        self._shader.setMatrix4f("viewMatrix", camera.projectionMatrix())
