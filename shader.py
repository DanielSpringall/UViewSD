from OpenGL import GL
import os


SHADER_DIR = os.path.join(os.path.dirname(__file__), "shaders")

class ShaderProgram:
    programShaderType = "program"
    vertexShaderType = "vertex"
    fragmentShaderType = "fragment"

    def __init__(self, vertexShaderName="default", fragmentShaderName="default"):
        self._vertexShaderName = vertexShaderName
        self._fragmentShaderName = fragmentShaderName
        self.programId = None

        self._setupShader()

    def _setupShader(self):
        vertexShaderString = self.loadShaderFromFile(
            self._vertexShaderName, self.vertexShaderType
        )
        vertexShader = GL.glCreateShader(GL.GL_VERTEX_SHADER)
        GL.glShaderSource(vertexShader, vertexShaderString)
        self._checkCompileErrors(vertexShader, self.vertexShaderType)

        fragmentShaderString = self.loadShaderFromFile(
            self._fragmentShaderName, self.fragmentShaderType
        )
        fragmentShader = GL.glCreateShader(GL.GL_FRAGMENT_SHADER)
        GL.glShaderSource(fragmentShader, fragmentShaderString)
        self._checkCompileErrors(fragmentShader, self.fragmentShaderType)

        self.programId = GL.glCreateProgram()
        GL.glAttachShader(self.programId, vertexShader)
        GL.glAttachShader(self.programId, fragmentShader)
        GL.glLinkProgram(self.programId)
        self._checkCompileErrors(self.programId, self.programShaderType)

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
        GL.glUseProgram(self.programId)

    @staticmethod
    def loadShaderFromFile(shaderName, shaderType):
        if shaderType not in [ShaderProgram.vertexShaderType, ShaderProgram.fragmentShaderType]:
            raise RuntimeError("{} is not a valid shader type.".format(shaderType))

        shaderFilePath = ""
        shaderExtension = ".{}".format(shaderType[:4])
        for fileName in os.listdir(SHADER_DIR):
            name, extension = os.path.splitext(fileName)
            if name == shaderName and extension == shaderExtension:
                shaderFilePath = os.path.join(SHADER_DIR, fileName)
                break
        else:
            raise RuntimeError("{} shader \"{}\" doesn't exist.".format(shaderType.capitalize(), shaderName))

        with open(shaderFilePath, 'r') as inFile:
            shaderString = inFile.read()
        return shaderString

    def setBool(self, name, value):
        GL.glUniform1i(GL.glGetUniformLocation(self.programId, name), int(bool(value)));

    def setInt(self, name, value):
        GL.glUniform1i(GL.glGetUniformLocation(self.programId, name), int(value))

    def setFloat(self, name, value):
        GL.glUniform1f(GL.glGetUniformLocation(self.programId, name), float(value))

    def setMatrix4f(self, name, value):
        GL.glUniformMatrix4fv(GL.glGetUniformLocation(self.programId, name), 1, GL.GL_FALSE, value); 
