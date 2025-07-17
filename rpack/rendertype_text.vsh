#version 150

#moj_import <minecraft:fog.glsl>

in vec3 Position;
in vec4 Color;
in vec2 UV0;
in ivec2 UV2;

uniform sampler2D Sampler2;

uniform mat4 ModelViewMat;
uniform mat4 ProjMat;
uniform int FogShape;

out float vertexDistance;
out vec4 vertexColor;
out vec2 texCoord0;

float a[320] = float[](3.4, 4.2, 5.0, 5.2, 1.1);

void main() {
    gl_Position = ProjMat * ModelViewMat * vec4(Position, 1.0);

    vertexDistance = fog_distance(Position, FogShape);
    vec4 color = Color;
    if ((Color.x * 255.0) == 178.0){ // #b299XX: notification color. will appear as white and blue channel will correspond to opacity
        if ((Color.y * 255.0) == 153.0){
                vec4 color = vec4(1.0,1.0,1.0,Color.z);
        }
    }
    vertexColor = color * texelFetch(Sampler2, UV2 / 16, 0);
    texCoord0 = UV0;
}
