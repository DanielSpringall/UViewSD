#version 330 core

out vec4 FragColor;
in vec2 uvs;
uniform float imageWidth;
uniform float imageHeight;

float gridSize = 10.0;


void main()
{
    vec2 uv = gl_FragCoord.xy / vec2(imageWidth, imageHeight) * vec2(imageWidth / imageHeight, 1.0);
    // float width = (gridSize * 1.2) / imageHeight;
    // uv = fract(uv * gridSize);
    // // abs version
    // float grid = max(
    //     1.0 - abs((uv.y - 0.5) / width),
    //     1.0 - abs((uv.x - 0.5) / width)
    // );

    // Output to screen (for shadertoy only)
    // gl_FragColor = vec4(grid, grid, grid, 1.0);
    gl_FragColor = vec4(uv.x, uv.y, 0.0, 1.0);
}
