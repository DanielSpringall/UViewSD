#version 330 core

layout (location = 0) in vec2 aPos;
uniform mat4 viewMatrix;

void main()
{
    gl_Position = viewMatrix * vec4(aPos.x, aPos.y, 0.0, 1.0);
};
