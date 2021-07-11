# Copyright 2021 by Daniel Springall.
# This file is part of UViewSD, and is released under the "MIT License Agreement".
# Please see the LICENSE file that should have been included as part of this package.
from OpenGL import GL
from PIL import Image


LINE_VERTEX_SHADER = """#version 330

layout (location = 0) in vec2 vPos;
uniform mat4 viewMatrix;

void main()
{
    gl_Position = viewMatrix * vec4(vPos.xy, 0.5, 1.0);
}
"""


LINE_FRAGMENT_SHADER = """#version 330

uniform vec3 color;
out vec4 fragColor;

void main()
{
    fragColor = vec4(color, 1.0);
}
"""


TEXTURE_VERTEX_SHADER = """#version 330

layout (location = 0) in vec2 vPos;

out vec2 uvCoords;
uniform mat4 viewMatrix;

void main()
{
    gl_Position = viewMatrix * vec4(vPos.xy, 0.5, 1.0);
    uvCoords = vPos.xy;
}
"""


TEXTURE_FRAGMENT_SHADER = """#version 330

in vec2 uvCoords;
out vec4 fragColor;

uniform sampler2D textureSampler;

void main()
{
    fragColor = texture(textureSampler, uvCoords);
}
"""


class BaseShader:
    def __init__(self, vertexShader, fragmentShader):
        self.programId = None
        self._vertexShader = vertexShader
        self._fragmentShader = fragmentShader
        self.bind()

    def bind(self):
        if self.programId:
            return

        vertexShader = GL.glCreateShader(GL.GL_VERTEX_SHADER)
        GL.glShaderSource(vertexShader, self._vertexShader)
        self._checkShaderErrors(vertexShader, "vertex")

        fragmentShader = GL.glCreateShader(GL.GL_FRAGMENT_SHADER)
        GL.glShaderSource(fragmentShader, self._fragmentShader)
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
    def __init__(self):
        BaseShader.__init__(
            self,
            vertexShader=LINE_VERTEX_SHADER,
            fragmentShader=LINE_FRAGMENT_SHADER,
        )


class TextureShader(BaseShader):
    def __init__(self, texturePath=None):
        self._textureId = None
        self._boundTexturePath = None
        BaseShader.__init__(
            self,
            vertexShader=TEXTURE_VERTEX_SHADER,
            fragmentShader=TEXTURE_FRAGMENT_SHADER,
        )
        if texturePath is not None:
            self.bindTexture(texturePath)

    def texturePath(self):
        return self._boundTexturePath

    def bindTexture(self, path):
        if path == self._boundTexturePath:
            return
        self._boundTexturePath = path

        if self._textureId is None:
            self._textureId = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._textureId)

        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
        GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_REPEAT)
        GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_REPEAT)

        image = Image.open(self._boundTexturePath)
        isRGBA = image.mode == "RGBA"
        tagetFormat = "RGBA" if isRGBA else "RGBX"
        imageData = image.tobytes("raw", tagetFormat, 0, -1)

        internalFormat = GL.GL_RGBA if isRGBA else GL.GL_RGB
        GL.glTexImage2D(
            GL.GL_TEXTURE_2D,
            0,
            internalFormat,
            image.size[0],
            image.size[1],
            0,
            GL.GL_RGBA,
            GL.GL_UNSIGNED_BYTE,
            imageData,
        )

    def use(self):
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._textureId)
        GL.glUseProgram(self.programId)

    def valid(self):
        """Return True if a texture has been bound."""
        return self._textureId is not None
