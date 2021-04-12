from ctypes import c_void_p
from shader import ShaderProgram
from OpenGL import GL
import numpy as np


class Shape:
    def __init__(self):
        self._shader = ShaderProgram()
        self._vao = None

        self._positions = 0
        self._indices = 0
        self._numVertices = 0

        self.setupMesh()

    def setupMesh(self):
        self._positions = np.array(
            [20.0, 20.0,
             20.0, 380.0,
             380.0, 20.0,
             380.0, 380.0], dtype=np.float32
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
        self._vao = GL.glGenVertexArrays(1)
        [vbo, ebo] = GL.glGenBuffers(2)

        GL.glBindVertexArray(self._vao)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vbo)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, self._positions.nbytes, self._positions, GL.GL_STATIC_DRAW)
        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, ebo)
        GL.glBufferData(GL.GL_ELEMENT_ARRAY_BUFFER, self._indices.nbytes, self._indices, GL.GL_STATIC_DRAW)

        GL.glVertexAttribPointer(0, 2, GL.GL_FLOAT, GL.GL_FALSE, 0, None)
        GL.glEnableVertexAttribArray(0)
        GL.glBindVertexArray(0); 

    def draw(self, camera):
        self._shader.use()
        self._shader.setMatrix4f("viewMatrix", camera.projectionMatrix())
        GL.glBindVertexArray(self._vao)
        GL.glDrawElements(GL.GL_TRIANGLES, self._numVertices, GL.GL_UNSIGNED_INT, c_void_p(0))
