from math import floor
from tkinter import Tk
from tkinter.filedialog import askopenfilename
import json
import os
import subprocess
import gzip
import base64
import io
import sys
import websocket
import re
from time import sleep
from PIL import Image

def gzip_and_base64_encode(data: bytearray) -> str:
    with io.BytesIO() as buf:
        with gzip.GzipFile(fileobj=buf, mode='wb') as gz:
            gz.write(data)
        compressed_data = buf.getvalue()
    encoded_data = base64.b64encode(compressed_data)
    return encoded_data.decode('utf-8')

def base64_and_gzip_decode(encoded_str: str) -> bytearray:
    compressed_data = base64.b64decode(encoded_str)
    with io.BytesIO(compressed_data) as buf:
        with gzip.GzipFile(fileobj=buf, mode='rb') as gz:
            decompressed_data = gz.read()
    return bytearray(decompressed_data)

def is_valid_gzip_base64_string(s: str) -> bool:
    try:
        compressed_data = base64.b64decode(s, validate=True)
        with io.BytesIO(compressed_data) as buf:
            with gzip.GzipFile(fileobj=buf, mode='rb') as gz:
                gz.read()
        return True
    except Exception:
        return False

def save_rgba_as_png(colors: list, size: int, path: str):
    img = Image.new('RGBA', (size, size))
    img.putdata([tuple(c) for c in colors])
    img.save(path, format='PNG')
    
def load_png_as_rgba(path: str) -> list:
    img = Image.open(path).convert('RGBA')
    return list(img.getdata())

def split_sprite_atlas(colors: list, size: int, txt_size) -> list:
    sprites = []

    for sy in range(size):
        for sx in range(size):
            sprite = []
            for row in range(txt_size):
                x = sx*txt_size
                y = sy*txt_size+row
                o = x+(y*size*txt_size)
                # print(sx, sy, x, y, row, o)
                sprite.extend(colors[o:(o+txt_size)])
            # print(sprite)
            sprites.append(sprite)

    return sprites

def parseTextureAtlas(index: dict) -> dict:
    final = [];
    textures = [];
    textures_8x8 = [];
    textures_4x4 = [];
    pixels_8x8 = [
        [(0, 0, 0, 0) for _ in range(index['size'] * index['size'] * 8 * 8)]
        for _ in range(len(index['atlases']))
    ]
    pixels_4x4 = [
        [(0, 0, 0, 0) for _ in range(index['size'] * index['size'] * 4 * 4)]
        for _ in range(len(index['atlases']))
    ]
    for atlas in index['atlases']:
        textures.extend(split_sprite_atlas(load_png_as_rgba(os.path.join(os.path.dirname(FILE_PATH), atlas)), index['size'], 16))
        textures_8x8.extend(split_sprite_atlas(load_png_as_rgba(os.path.join(os.path.dirname(FILE_PATH), "small_"+atlas)), index['size'], 8))
        textures_4x4.extend(split_sprite_atlas(load_png_as_rgba(os.path.join(os.path.dirname(FILE_PATH), "tiny_"+atlas)), index['size'], 4))
    textures = textures[0:index['length']]
    textures_8x8 = textures_8x8[0:index['length']]
    textures_4x4 = textures_4x4[0:index['length']]
    # print(textures)
    for textureInd, texture, texture_8x8, texture_4x4 in zip(range(len(textures)), textures, textures_8x8, textures_4x4):
        data = [0] * (32 * 3);
        palette = [(0,0,0,0)]
        seencolors = {(0,0,0,0): 0}
        texture_data = texture
        if index['use_resized']:
            texture_data.extend(texture_8x8)
            texture_data.extend(texture_4x4)
        for color in texture_data:
            if color not in seencolors:
                if len(palette) < 33:
                    seencolors[color] = len(palette);
                    data[len(palette)*3-3] = color[0];
                    data[len(palette)*3-2] = color[1];
                    data[len(palette)*3-1] = color[2];
                    palette.append(color)
                else:
                    seencolors[color] = 32
                    palette.append(color)
            data.append(seencolors[color])
        if not index['use_resized']:
            #resizing to 8x8
            for sy in range(8):
                for sx in range(8):
                    mostUsed = 0
                    mostUsedAmt = 0
                    used = {}
                    ranges = [(sx*2,sy*2), (sx*2+1,sy*2), (sx*2,sy*2+1), (sx*2+1,sy*2+1)]
                    for rangeGet in ranges:
                        colorInd = data[96 + (rangeGet[1]*16 + rangeGet[0])]
                        if colorInd == 0:
                            continue
                        if colorInd not in used:
                            used[colorInd] = 0
                        used[colorInd] += 1;
                        if used[colorInd] > mostUsedAmt:
                            mostUsed = colorInd
                            mostUsedAmt = used[colorInd]
                    data.append(mostUsed)
                    size = index['size']
                    atlasInd = textureInd//(size*size);
                    inAtlasInd = textureInd%(size*size)
                    pixels_8x8[atlasInd][((((inAtlasInd)//size)*8+sy)*size*8)+sx+((inAtlasInd%size)*8)] = palette[mostUsed];
            #resizing to 4x4
            for sy in range(4):
                for sx in range(4):
                    mostUsed = 0
                    mostUsedAmt = 0
                    used = {}
                    ranges = []
                    for addRangeX in range(4):
                        for addRangeY in range(4):
                            ranges.append((sx*4+addRangeX,sy*4+addRangeY))
                    for rangeGet in ranges:
                        colorInd = data[96 + (rangeGet[1]*16 + rangeGet[0])]
                        if colorInd == 0:
                            continue
                        if colorInd not in used:
                            used[colorInd] = 0
                        used[colorInd] += 1;
                        if used[colorInd] > mostUsedAmt:
                            mostUsed = colorInd
                            mostUsedAmt = used[colorInd]
                    data.append(mostUsed)
                    size = index['size']
                    atlasInd = textureInd//(size*size);
                    inAtlasInd = textureInd%(size*size)
                    pixels_4x4[atlasInd][((((inAtlasInd)//size)*4+sy)*size*4)+sx+((inAtlasInd%size)*4)] = palette[mostUsed];
        # print(gzip_and_base64_encode(bytearray(data)))
        # print(data)
        final.append(gzip_and_base64_encode(bytearray(data)))
    if not index['use_resized']:
        print("Saving new resizes...");
        for atlas, image8x8, image4x4 in zip(index['atlases'], pixels_8x8, pixels_4x4):
            save_rgba_as_png(image8x8, index['size']*8, os.path.join(os.path.dirname(FILE_PATH), "small_"+atlas))
            save_rgba_as_png(image4x4, index['size']*4, os.path.join(os.path.dirname(FILE_PATH), "tiny_"+atlas))
    return final
        


def loadConfig():
    global config
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_file_path = os.path.join(script_dir, 'config.json')
    if not os.path.exists(config_file_path):
        config = {
            'token': None,
            'deletebin': False
        }
        saveConfig();
        return;
    with open(config_file_path, 'r') as file:
        config = json.load(file)
def saveConfig():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_file_path = os.path.join(script_dir, 'config.json')
    with open(config_file_path, 'w') as file:
        json.dump(config, file);

def chunk_list(lst, chunk_size):
    return [lst[i:i+chunk_size] for i in range(0, len(lst), chunk_size)]

def sanitize_for_snbt(s: str) -> str:
    # Replace backslash first to avoid double escaping
    s = s.replace('\\', '\\\\')
    # Escape double quotes
    s = s.replace('"', '\\"')
    # Escape newlines, tabs, carriage returns, etc.
    s = s.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
    s = re.sub(r'[\x00-\x1F]', lambda m: f'\\u{ord(m.group(0)):04x}', s)  # escape other control characters

    return f'"{s}"'

small = [bytearray()]
large = []

def check_arrays():
    global small, large
    if len(small[-1]) >= MAX_LENGTH_PER_BLOCK:
        small.append(bytearray())

Tk().withdraw()
FILE_PATH = askopenfilename()
MAX_LENGTH_PER_BLOCK = 2000
WANTED_SEND_CHANNELS = 1
try:
    WANTED_SEND_CHANNELS = int(input("How many send channels? type enter for 1. "))
except:
    pass
SEND_CHANNELS = 1


name = FILE_PATH.split("_")[1]
obj = {}
identcount = 0
with open(FILE_PATH, 'r', encoding='utf-8') as f:
    obj = json.load(f)
    if os.path.basename(FILE_PATH) == ".index":
        obj = parseTextureAtlas(obj);
    
def serialize_value(value: str) -> bytearray:
    if is_valid_gzip_base64_string(value):
        return base64_and_gzip_decode(value)
    return bytearray(value.encode('utf-8'))

if isinstance(obj, dict):
    print("parsing dict!")
    for key_str, value_str in obj.items():
        key = key_str.encode('utf-8')
        value = serialize_value(value_str)
        if len(key) + len(value) + 100 > MAX_LENGTH_PER_BLOCK: # large
            large.append(bytearray(key))
            check_arrays()
            large.append(value)
            check_arrays()
        else: #small
            if len(small[-1]) + len(key) + len(value) + 2 > MAX_LENGTH_PER_BLOCK:
                small.append(bytearray())
            small[-1].append(floor(len(key) / 128))
            small[-1].append(len(key) % 128)
            small[-1].extend(key)
            small[-1].append(floor(len(value) / 128))
            small[-1].append(len(value) % 128)
            small[-1].extend(value)
            check_arrays()
if isinstance(obj, list):
    print("parsing list!")
    large = None
    for value_str in obj:
        value = bytearray();
        if isinstance(value_str, dict) or isinstance(value_str, list):
            value_str = json.dumps(value_str);
            value = bytearray(value_str.encode('utf-8'))
        else:
            value = serialize_value(value_str)
        sumg = 0;
        for g in bytearray(value):
            sumg += g;
        # print(f"Sum: {sumg
        if len(value) + 100 > MAX_LENGTH_PER_BLOCK: # large
            small.append(bytearray())
            small[-1].append(floor(len(value) / 128))
            small[-1].append(len(value) % 128)
            small[-1].extend(value)
            check_arrays()
        else: #small
            if len(small[-1]) + len(value) + 100 > MAX_LENGTH_PER_BLOCK:
                small.append(bytearray())
            small[-1].append(floor(len(value) / 128))
            small[-1].append(len(value) % 128)
            small[-1].extend(value)
            check_arrays()

# print(f"Large: {large}\n\n\nSmall: {small}")
print("Done parsing json.")

print("(CC) Connecting to CodeClient...");


ws = None;
loadConfig();
try:
    ws = websocket.create_connection("ws://localhost:31375")
    print("(CC) Connected.");
except Exception as e:
    print(f"(CC) Socket failed to connect: {e}")
    sys.exit(1)
    

if config['token'] != None:
    ws.send(config['token']);
    if ws.recv() != "auth":
        print("(CC) Token expired, getting new token")
        config['token'] = None

if config['token'] == None:
    ws.send("token")
    token = ws.recv();
    config['token'] = token;
    print("(CC) Please authorize the app's permission ingame.");
    ws.send("scopes inventory read_plot write_code");
    if ws.recv() != "auth":
        raise Exception("(CC) Unauthorized permission from client.");
    print("(CC) CodeClient token authorized successfully.")
saveConfig();


sendQueue = []
sendQueue.append(len(small))
sendQueue.extend([gzip_and_base64_encode(e) for e in small])
if large != None:
    sendQueue.append(len(large))
    sendQueue.extend([gzip_and_base64_encode(e) for e in large])
previous = ""

originalLength = len(sendQueue)
while True:
    if len(sendQueue) == 0:
        break
    ws.send('inv');
    invsave = ws.recv();
    print(f"\r({originalLength-len(sendQueue)}/{originalLength}) Waiting For Receival...", end="")
    # print(previous == invsave);
    # print(invsave);
    if (not (""""hypercube:auth":"Ԕ֐ļЕΚӰԾԾȒɁ\"""" in invsave)) or previous == invsave:
        sleep(0.02)
        continue;
    print(f"\r({originalLength-len(sendQueue)}/{originalLength}) Sending Message...", end="")
    previous = invsave
    channelsrequested = SEND_CHANNELS
    match = re.search(r"Waiting For Data:\s*(\d+)", invsave)
    if match:
        channelsrequested = int(match.group(1))
    if "Waiting For Data: -1" in invsave:
        channelsrequested = 1;
    sendchannels = min(SEND_CHANNELS, channelsrequested)
    SEND_CHANNELS = min(SEND_CHANNELS + 1, WANTED_SEND_CHANNELS)
    send = [str(e) for e in sendQueue[:sendchannels]]
    sendQueue = sendQueue[sendchannels:]
    sendNBT = []
    for i, msg in enumerate(send):
        sendNBT.append(f'"hypercube:data{i+1}":{sanitize_for_snbt(msg)}')
    newinv = """[{Slot:0b,components:{"minecraft:custom_data":{PublicBukkitValues:{""" + ','.join(sendNBT) + """}},"minecraft:custom_name":'{"color":"aqua","italic":false,"text":"Data"}'},count:1,id:"minecraft:soul_lantern"}]"""
    ws.send('setinv ' + newinv);
    sleep(0.02)
print(f"\rDone.")

if ws != None:
    ws.close()