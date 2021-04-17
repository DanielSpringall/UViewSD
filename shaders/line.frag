#version 330 core

precision mediump float;
varying vec3 colour;

void main()
{
    gl_FragColor = vec4(colour, 1.0);
}
