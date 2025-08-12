#version 150

in vec3 Position;
in vec4 Color;

uniform mat4 ModelViewMat;
uniform mat4 ProjMat;
uniform float GameTime;

out vec4 vertexColor;

vec4 intToColorNerd(int n) {
    return vec4(float((n >> 8) & 0x0F) / 15.0, float((n >> 4) & 0x0F) / 15.0, float(n & 0x0F) / 15.0, 1);
}

vec4 intToColor(int n) { //For values between 0-999
    return vec4(float((n / 100) % 10) * 10 / 255.0, float((n / 10) % 10) * 10 / 255.0, float(n % 10) * 10 / 255.0, 1);
}

vec4 intToColorHighPrecision(int n) { //For values between 0-999999
    return vec4(float((n / 10000) % 100) / 255.0, float((n / 100) % 100) / 255.0, float(n % 100) / 255.0, 1);
}
void main() {
    vec4 color = Color;
    vec3 position = Position;
    if (Position.z == 0) { // GUI Container Overlay
        int wInt = int(Color.w * 255.0);
        if (Color.x == 16.0/255.0 && Color.y == 16.0/255.0 && Color.z == 16.0/255.0) {
            color.w = 0;
        } else if (Color.x == 0 && Color.y == 0 && Color.z == 0) { //Chatbox opened
            color = vec4(0.05, 0.05, 0.05, 0.85);
            // color = vec4(Color.x, Color.x, Color.x, 1);
        }
    }
    if (int(Position.z) == 2600) { //Chatbox unopened
        color = vec4(0.05, 0.05, 0.05, 0.85);
        int h = 0;
        float g = mod(GameTime * 24000.0, 1.0) / 20.0;
        float t = min((Color.w / 0.3) - g, 1);
        // color = intToColorHighPrecision(int(GameTime * 24000));
        position.x *= t*t;
    }
    gl_Position = ProjMat * ModelViewMat * vec4(position, 1.0);
    vertexColor = color;
}
