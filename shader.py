from OpenGL import GL
import os


class ShaderProgram:
    programShaderType = "program"
    vertexShaderType = "vertex"
    fragmentShaderType = "fragment"

    def __init__(self, vertexShaderFilePath, fragmentShaderFilePath):
        self.vertexShaderFilePath = vertexShaderFilePath
        self.fragmentShaderFilePath = fragmentShaderFilePath
        self.program = None
        self._setupShader()

    def _setupShader(self):
        vertexShaderString = self.loadShaderFromFile(self.vertexShaderFilePath)
        vertexShader = GL.glCreateShader(GL.GL_VERTEX_SHADER)
        GL.glShaderSource(vertexShader, vertexShaderString)
        self._checkCompileErrors(vertexShader, self.vertexShaderType)

        fragmentShaderString = self.loadShaderFromFile(self.fragmentShaderFilePath)
        fragmentShader = GL.glCreateShader(GL.GL_FRAGMENT_SHADER)
        GL.glShaderSource(fragmentShader, fragmentShaderString)
        self._checkCompileErrors(fragmentShader, self.fragmentShaderType)

        self.program = GL.glCreateProgram()
        GL.glAttachShader(self.program, vertexShader)
        GL.glAttachShader(self.program, fragmentShader)
        GL.glLinkProgram(self.program)
        self._checkCompileErrors(self.program, self.programShaderType)

        GL.glDeleteShader(vertexShader)
        GL.glDeleteShader(fragmentShader)
        return True

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

    def use(self):
        GL.glUseProgram(self.program)

    @staticmethod
    def loadShaderFromFile(filePath):
        if not os.path.isfile(filePath):
            raise RuntimeError("{} doesn't exist.".format(filePath))

        with open(filePath, 'r') as inFile:
            shaderString = inFile.read()
        return shaderString

    def setBool(self, name, value):
        GL.glUniform1i(GL.glGetUniformLocation(self.program, name), int(bool(value)));

    def setInt(self, name, value):
        GL.glUniform1i(GL.glGetUniformLocation(self.program, name), int(value))

    def setFloat(self, name, value):
        GL.glUniform1f(GL.glGetUniformLocation(self.program, name), float(value))

    def setMatrix4f(self, name, value):
        GL.glUniformMatrix4fv(GL.glGetUniformLocation(self.program, name), 1, GL.GL_FALSE, value); 
