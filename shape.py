from shader import ShaderProgram
from OpenGL import GL
import numpy as np


class Shape:
    def __init__(self):
        self._shader = None
        self._vao = None

        self._vertices = 0
        self._vertIndices = 0
        self._numVertices = 0

        self.setupShader()
        self.setupMesh()

    def setupShader(self):
        self._shader = ShaderProgram(
            "C:\\Users\\Daniel\\Projects\\Python\\uvViewer\\shaders\\default.vert",
            "C:\\Users\\Daniel\\Projects\\Python\\uvViewer\\shaders\\default.frag"
        )

    def setupMesh(self):
        self._vertices = np.array([0, 0, 0, 400, 400, 0, 400, 400], dtype=np.float32)
        self._vertIndices = np.array([0, 1, 2, 1, 2, 3], np.int)
        self._numVertices = len(self._vertIndices)

        self._vao = GL.glGenVertexArrays(1)
        [vbo, ebo] = GL.glGenBuffers(2)

        GL.glBindVertexArray(self._vao)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vbo)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, self._vertices.nbytes, self._vertices, GL.GL_STATIC_DRAW)
        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, ebo)
        GL.glBufferData(GL.GL_ELEMENT_ARRAY_BUFFER, self._vertIndices.nbytes, self._vertIndices, GL.GL_STATIC_DRAW)

        GL.glVertexAttribPointer(0, 2, GL.GL_FLOAT, GL.GL_FALSE, 0, None)
        GL.glEnableVertexAttribArray(0)

        GL.glBindVertexArray(0); 

        """
        // ..:: Initialization code :: ..
        // 1. bind Vertex Array Object
        glBindVertexArray(VAO);
        // 2. copy our vertices array in a vertex buffer for OpenGL to use
        glBindBuffer(GL_ARRAY_BUFFER, VBO);
        glBufferData(GL_ARRAY_BUFFER, sizeof(vertices), vertices, GL_STATIC_DRAW);
        // 3. copy our index array in a element buffer for OpenGL to use
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO);
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, sizeof(indices), indices, GL_STATIC_DRAW);
        // 4. then set the vertex attributes pointers
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * sizeof(float), (void*)0);
        glEnableVertexAttribArray(0);  

        [...]
        
        // ..:: Drawing code (in render loop) :: ..
        glUseProgram(shaderProgram);
        glBindVertexArray(VAO);
        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, 0)
        glBindVertexArray(0);
        """

    def original(self):
        vertices = np.array([0, 400, 0, 0, 400, 0, 400, 0, 0, 400, 400, 400], dtype=np.float32)

        self._vao = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._vao)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL.GL_STATIC_DRAW)

        GL.glEnableVertexAttribArray(0)
        GL.glVertexAttribPointer(0, 2, GL.GL_FLOAT, GL.GL_FALSE, 0, None)

    def draw(self, camera):
        self._shader.use()
        self._shader.setMatrix4f("viewMatrix", camera.projectionMatrix())

        GL.glBindVertexArray(self._vao)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, 6)
        return
        # GL.glDrawElements(GL.GL_TRIANGLES, self._numVertices, GL.GL_UNSIGNED_INT, 0)
