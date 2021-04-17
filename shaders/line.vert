#version 330 core

layout (location = 0) in vec2 vPos;
uniform mat4 viewMatrix;
uniform vec3 vColour;

out vec3 colour;

void main()
{
    colour = vColour;
    gl_Position = viewMatrix * vec4(vPos.xy, 0.5, 1.0);
};
