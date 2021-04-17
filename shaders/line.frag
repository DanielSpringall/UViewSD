#version 330 core

in vec3 lineColour;

void main()
{
    gl_FragColor = vec4(lineColour, 1.0);
}
