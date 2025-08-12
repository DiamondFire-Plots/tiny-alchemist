#version 150

#moj_import <minecraft:fog.glsl>

in vec3 Position;
in vec4 Color;
in vec2 UV0;
in ivec2 UV2;

uniform sampler2D Sampler0;
uniform sampler2D Sampler2;

uniform mat4 ModelViewMat;
uniform mat4 ProjMat;
uniform int FogShape;
uniform vec2 ScreenSize;
uniform float GameTime;

out float vertexDistance;
out vec4 vertexColor;
out vec2 texCoord0;

vec4 colorPalette[16] = vec4[](
    vec4(1.0, 1.0, 1.0, 1.0), vec4(1.0, 0.0, 1.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0),
    vec4(0.0, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 
    vec4(0.0, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), 
    vec4(0.0, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0), vec4(0.0, 0.0, 0.0, 1.0)
); 

int overlayBottomY = 63;
int overlayTopY = 71;

int actionBarZ = 2200;

vec4 intToColorHighPrecision(int n) { //For values between 0-999999
    return vec4(float((n / 10000) % 100) / 255.0, float((n / 100) % 100) / 255.0, float(n % 100) / 255.0, 1);
}

vec4 intToColor(int n) { //For values between 0-999
    return vec4(float((n / 100) % 10) * 10 / 255.0, float((n / 10) % 10) * 10 / 255.0, float(n % 10) * 10 / 255.0, 1);
}

float erp(float x, float y, float s) {
    return (x*(1-s)) + (y*(s));
}

void main() {
    vec4 color = Color;
    vec3 position = Position;
    texCoord0 = UV0;
    // if (color.x * 255.0 >= 1.0 && color.x * 255.0 <= 16.0 && color.y * 255.0 >= 1.0 && color.y * 255.0 <= 4.0 && color.z * 255.0 >= 1.0 && color.z * 255.0 <= 4.0) {
    //     color = colorPalette[4*(int(Color.y * 255.0) - 1) + (int(Color.z * 255.0) - 1)];

    //     color.x = float((zInt >> 8) & 0x0F) / 15.0;
    //     color.y = float((zInt >> 4) & 0x0F) / 15.0;
    //     color.z = float(zInt & 0x0F) / 15.0;
    //     color.w = (Color.x * 17.0) - (1 / 15);
    // }
    if (int(Position.z) == actionBarZ) { //action bar
        if (color.y == 0) {
            if (int(color.z*255.0) >= 1) {
                bool increasing = int(color.z*255.0) < 128;
                vec3 bottomRightPosition = (inverse(ModelViewMat) * inverse(ProjMat) * vec4(1, -1, 0, 1)).xyz;
                // bool isLeft = UV0.x * 100 < 100/255.0;
                // bool isTop = UV0.y * 100 < 20/255.0;
                vec4 textureColorHighAccuracy = texture(Sampler0, UV0);
                int colorGet = int(textureColorHighAccuracy.r * 255.0);
                bool isTop = colorGet == 255 || colorGet == 254;
                bool isLeft = colorGet == 255 || colorGet == 253;

                // vec3 centerPosition = (inverse(ModelViewMat) * inverse(ProjMat) * vec4(0, 0, 0, 1)).xyz;
                float setX = 0;
                if (isLeft) {
                    setX = 0;
                } else {
                    setX = bottomRightPosition.x;
                }
                float setY = 0;
                if (isTop) {
                    setY = 0;
                } else {
                    setY = bottomRightPosition.y;
                }
                float t = Color.r * 255.0 / 20.0;
                if (increasing) {
                    t = 1-t;
                }
                t = t*t*t;
                if (increasing) {
                    t = 1-t;
                }
                
                // position.x = (setX * t) + (centerPosition.x * (1-t));
                // position.y = (setY * t) + (centerPosition.y * (1-t));
                // position.y = (setY * t) + (bottomRightPosition.y * (1-t));
                position.x = setX;
                position.y = setY;
                position.z = 0;
                // color = intToColor(colorGet);
                // if (colorGet == 25) {
                //     color = vec4(1,0,1,1);
                // }
                // color.a = 10;
                color = vec4(0.05, 0.05, 0.05, t*0.85);
                // texCoord0.x += 0.001;
                // if (isTop) {
                //     color = vec4(1, 0, 1, 1);
                // }
                // color = vec4(UV0.x*100, UV0.y*100, 1, 1);
                
            } else { //discard too
                color.w = 0;
            }
        } else if (int(color.y * 255.0) == 180) {
            float tx = color.x;
            tx = 1-((1-tx)*(1-tx));
            float g = mod(GameTime*3000.0, 10) / 10.0 * 6.283;
            position.y += sin(g) * 2;
            position.y += 15;
            float t = (int(color.z * 255.0)%21) / 20.0;
            if (int(color.z * 255.0) < 21) {
                t = 1-t;
            }
            t = t*t*t;
            if (int(color.z * 255.0) < 21) {
                t = 1-t;
            }
            position.y += t * 70;
            color = vec4(143.0/255.0, 97.0/255.0, 97.0/255.0, tx);
            // float brighten = abs(mod(GameTime*24000.0*5, 700)-mod(position.x-50,700));
            // if (brighten < 20) {
            //     color = vec4(1,1,1,tx);
            // } else if (brighten <= 40) {
            //     float c = 1 - ((brighten - 20) / 20.0);
            //     color = vec4(erp(color.r, 1.0, c), erp(color.g, 1.0, c), erp(color.b, 1.0, c), tx);
            // }
        } else if (color.x == 0 && int(color.y * 255.0) == 181) {
            float t = (int(color.z * 255.0)%21) / 20.0;
            if (int(color.z * 255.0) < 21) {
                t = 1-t;
            }
            t = t*t*t;
            if (int(color.z * 255.0) < 21) {
                t = 1-t;
            }
            position.y += t * 40;
            color = vec4(1, 1, 1, 1-t);
        }  else if (color.x < 1 && color.y < 1 && color.z < 1) {
            color.w = 0;
        } 
        // position.y += 50;
        // position.y -= 1;
        // centerPosition = vec3(ScreenSize.x / 3 / 2, ScreenSize.y / 3 / 2, 0);
        // int uiScale = int(ScreenSize.x / (inverse(ModelViewMat) * inverse(ProjMat) * vec4(1, 0, 0, 1)).x);
        // if (true) {
        //     vec4 viewSize = vec4(ScreenSize.x, ScreenSize.y, 1, 1) * ProjMat;
        //     int ig = (int(ScreenSize.y)/2) - (int(position.y)*1);
        //     ig = int(distance(vec2(centerPosition.x, centerPosition.y), vec2(position.x, position.y)));
        //     ig = int(bottomRightPosition.y) - int(Position.y);
        //     ig = int(Position.x) - int(centerPosition.x);
        //     color.x = float((ig >> 8) & 0x0F) / 15.0;
        //     color.y = float((ig >> 4) & 0x0F) / 15.0;
        //     color.z = float(ig & 0x0F) / 15.0;
        //     // if (ig >= 17*3 && ig <= 23*3) {
        //     //     color = vec4(1,1,1,1);
        //     // }
        //     // float scale = 1 / (uiScale + 0.0);
        //     // color = vec4(scale, scale, scale, 1);
        //     color.w = 1;
        // }
        // vec2 is = checkOverlay(int(Position.x - 1), int(Position.y - 1));
        // if (abs(is.x) + abs(is.y) >= 2) {
        //     color.w = 1;
        //     if (is.x == -1 && is.y == 1) {
        //         position.x = centerPosition.x;
        //         position.y = centerPosition.y;
        //     }
        // }
        // vec2 i = checkOverlay(int(Position.x), int(Position.y));
        // if (abs(i.x) + abs(i.y) >= 2) {
        //     vec4 viewSize = vec4(ScreenSize.x, ScreenSize.y, 1, 1) * ProjMat;
        //     color = vec4(0.05, 0.05, 0.05, Color.r*0.5);
        //     // positionOffset.x = i.x * Color.r;
        //     // positionOffset.y = -i.y * Color.r;
        //     // overridePosition = true;

            
        //     if (i.x == -1 && i.y == 1) {
        //     }
        // }

        
        // position.y -= 262;
        // position.x += 91;

        // position.y -= int(color.x * 255.0);
        // color = colorPalette[1];
    }
    gl_Position = ProjMat * ModelViewMat * vec4(position, 1.0);
    vertexDistance = fog_distance(Position, FogShape);
    vertexColor = color * texelFetch(Sampler2, UV2 / 16, 0);
}