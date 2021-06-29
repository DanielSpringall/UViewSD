# Copyright 2021 by Daniel Springall.
# This file is part of UViewSD, and is released under the "MIT License Agreement".
# Please see the LICENSE file that should have been included as part of this package.
from OpenGL import GL


VERTEX_SHADER = """#version 330

layout (location = 0) in vec2 vPos;
uniform mat4 viewMatrix;

void main()
{
    gl_Position = viewMatrix * vec4(vPos.xy, 0.5, 1.0);
}
"""


FRAGMENT_SHADER = """#version 330

uniform vec3 color;
out vec4 fragColor;

void main()
{
    fragColor = vec4(color, 1.0);
}
"""


class LineShader:
    def __init__(self):
        self.programId = None
        self._bind()

    def _bind(self):
        vertexShader = GL.glCreateShader(GL.GL_VERTEX_SHADER)
        GL.glShaderSource(vertexShader, VERTEX_SHADER)
        self._checkShaderErrors(vertexShader, "vertex")

        fragmentShader = GL.glCreateShader(GL.GL_FRAGMENT_SHADER)
        GL.glShaderSource(fragmentShader, FRAGMENT_SHADER)
        self._checkShaderErrors(fragmentShader, "fragment")

        self.programId = GL.glCreateProgram()
        GL.glAttachShader(self.programId, vertexShader)
        GL.glAttachShader(self.programId, fragmentShader)
        GL.glLinkProgram(self.programId)
        self._checkShaderErrors(self.programId, "program", isProgramShader=True)

        GL.glDetachShader(self.programId, vertexShader)
        GL.glDetachShader(self.programId, fragmentShader)
        GL.glDeleteShader(vertexShader)
        GL.glDeleteShader(fragmentShader)
        return True

    def setVec3f(self, name, value):
        GL.glUniform3fv(GL.glGetUniformLocation(self.programId, name), 1, value)

    def setMatrix4f(self, name, value):
        GL.glUniformMatrix4fv(GL.glGetUniformLocation(self.programId, name), 1, GL.GL_FALSE, value)

    def use(self):
        GL.glUseProgram(self.programId)

    @staticmethod
    def _checkShaderErrors(shader, shaderName, isProgramShader=False):
        getivMethod = GL.glGetProgramiv if isProgramShader else GL.glGetShaderiv
        statusToCheck = GL.GL_LINK_STATUS if isProgramShader else GL.GL_COMPILE_STATUS
        if getivMethod(shader, statusToCheck):
            return

        getInfoMethod = GL.glGetProgramInfoLog if isProgramShader else GL.glGetShaderInfoLog
        info = getInfoMethod(shader)
        if info:
            failType = "shader linking" if isProgramShader else "{} shader compilation".format(shaderName)
            raise RuntimeError("Failed {}: {}".format(failType, info))
