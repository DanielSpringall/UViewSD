#version 330 core

precision mediump float;
uniform vec3 colour;

void main()
{
    gl_FragColor = vec4(colour, 1.0);
}
