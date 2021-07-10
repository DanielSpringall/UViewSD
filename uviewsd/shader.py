# Copyright 2021 by Daniel Springall.
# This file is part of UViewSD, and is released under the "MIT License Agreement".
# Please see the LICENSE file that should have been included as part of this package.
from OpenGL import GL


class BaseShader:
    def __init__(self):
        self.programId = None
        self.bind()

    def bind(self):
        if self.programId:
            return

        vertexShader = GL.glCreateShader(GL.GL_VERTEX_SHADER)
        GL.glShaderSource(vertexShader, self.vertexShader())
        self._checkShaderErrors(vertexShader, "vertex")

        fragmentShader = GL.glCreateShader(GL.GL_FRAGMENT_SHADER)
        GL.glShaderSource(fragmentShader, self.fragmentShader())
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
        GL.glUniformMatrix4fv(
            GL.glGetUniformLocation(self.programId, name), 1, GL.GL_FALSE, value
        )

    def use(self):
        GL.glUseProgram(self.programId)

    @staticmethod
    def _checkShaderErrors(shader, shaderName, isProgramShader=False):
        getivMethod = GL.glGetProgramiv if isProgramShader else GL.glGetShaderiv
        statusToCheck = GL.GL_LINK_STATUS if isProgramShader else GL.GL_COMPILE_STATUS
        if getivMethod(shader, statusToCheck):
            return

        getInfoMethod = (
            GL.glGetProgramInfoLog if isProgramShader else GL.glGetShaderInfoLog
        )
        info = getInfoMethod(shader)
        if info:
            failType = (
                "shader linking"
                if isProgramShader
                else "{} shader compilation".format(shaderName)
            )
            raise RuntimeError("Failed {}: {}".format(failType, info))

    @staticmethod
    def vertexShader():
        raise NotImplementedError()

    @staticmethod
    def fragmentShader():
        raise NotImplementedError()


class LineShader(BaseShader):
    @staticmethod
    def vertexShader():
        return """#version 330

layout (location = 0) in vec2 vPos;
uniform mat4 viewMatrix;

void main()
{
    gl_Position = viewMatrix * vec4(vPos.xy, 0.5, 1.0);
}
"""

    @staticmethod
    def fragmentShader():
        return """#version 330

uniform vec3 color;
out vec4 fragColor;

void main()
{
    fragColor = vec4(color, 1.0);
}
"""


class TextureShader(BaseShader):
    @staticmethod
    def vertexShader():
        return """#version 330

in vec2 position;
out vec2 OutTexCoords;

void main()
{
    gl_Position = vec4(position, 0.0, 1.0);
    OutTexCoords = position;
}
"""

    @staticmethod
    def fragmentShader():
        return """#version 330

in vec2 OutTexCoords;
uniform sampler2D samplerTex;
out vec4 fragColor;

void main()
{
    fragColor = texture(samplerTex, OutTexCoords);
}
"""
