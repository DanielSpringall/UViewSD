# Copyright 2021 by Daniel Springall.
# This file is part of UViewSD, and is released under the "MIT License Agreement".
# Please see the LICENSE file that should have been included as part of this package.
from OpenGL import GL


VERTEX_SHADER = """#version 330 core

layout (location = 0) in vec2 vPos;
uniform mat4 viewMatrix;

void main()
{
    gl_Position = viewMatrix * vec4(vPos.xy, 0.5, 1.0);
};
"""


FRAGMENT_SHADER = """#version 330 core

precision mediump float;
uniform vec3 color;

void main()
{
    gl_FragColor = vec4(color, 1.0);
}
"""

lineShader = None
def getLineShader():
    global lineShader
    if lineShader is None:
        lineShader = ShaderProgram()
    return lineShader


class ShaderProgram:
    programShaderType = "program"
    vertexShaderType = "vertex"
    fragmentShaderType = "fragment"

    def __init__(self):
        self.programId = None
        self._setupShader()

    def _setupShader(self):
        vertexShader = GL.glCreateShader(GL.GL_VERTEX_SHADER)
        GL.glShaderSource(vertexShader, VERTEX_SHADER)
        self._checkCompileErrors(vertexShader, self.vertexShaderType)

        fragmentShader = GL.glCreateShader(GL.GL_FRAGMENT_SHADER)
        GL.glShaderSource(fragmentShader, FRAGMENT_SHADER)
        self._checkCompileErrors(fragmentShader, self.fragmentShaderType)

        self.programId = GL.glCreateProgram()
        GL.glAttachShader(self.programId, vertexShader)
        GL.glAttachShader(self.programId, fragmentShader)
        GL.glLinkProgram(self.programId)
        self._checkCompileErrors(self.programId, self.programShaderType)

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
    def _checkCompileErrors(shader, shaderType):
        # TODO: Work out why this isn't working...
        return
        isProgramShader = shaderType == ShaderProgram.programShaderType
        statusToCheck = GL.GL_LINK_STATUS if isProgramShader else GL.GL_COMPILE_STATUS
        if GL.glGetShaderiv(shader, statusToCheck) == GL.GL_TRUE:
            return

        info = GL.glGetProgramInfoLog(shader) if isProgramShader else GL.glGetShaderInfoLog(shader)
        failType = "Shader linking" if isProgramShader else "{} shader compilation".format(shaderType.capitalize())
        raise RuntimeError("{} failed: {}".format(failType, info))
