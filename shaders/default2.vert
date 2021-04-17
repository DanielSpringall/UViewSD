#version 330 core

layout (location = 0) in vec2 aPos;
layout (location = 1) in vec2 uvPos;
uniform mat4 viewMatrix;
out vec2 uvs;

void main()
{
    uvs = uvPos;
    gl_Position = viewMatrix * vec4(aPos.x, aPos.y, 0.0, 1.0);
};
