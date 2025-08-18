import json
import os
import shutil
import time
import subprocess
import gzip
import base64
import io
import sys
import websocket
import re
from time import sleep
from PIL import Image

def chunk_list(data, block_size):
    return [data[i:i+block_size] for i in range(0, len(data), block_size)]

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
    
def load_png_as_rgba(path: str) -> list:
    img = Image.open(path).convert('RGBA')
    return list(img.getdata())

def textureToGzip(path: str) -> str:
    texture = load_png_as_rgba(path)
    # print(textures)
    data = [0] * (32 * 3);
    palette = [(0,0,0,0)]
    seencolors = {(0,0,0,0): 0}
    texture_data = texture
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
    return gzip_and_base64_encode(bytearray(data))


LIST_PATH = r"K:\Programming\GitHub\tiny-alchemist\scripts\lapgc\materials.txt"
MODELS_PATH = r"C:\Users\User\AppData\Roaming\PrismLauncher\instances\DiamondFire\minecraft\resourcepacks\main1.21.3\assets\minecraft\models"
TEXTURES_PATH = r"C:\Users\User\AppData\Roaming\PrismLauncher\instances\DiamondFire\minecraft\resourcepacks\main1.21.3\assets\minecraft\textures"
OUTPUT_PATH_TEXTURES = r"K:\Programming\GitHub\tiny-alchemist\scripts\lapgc\lvimport_textures.json"
OUTPUT_PATH_MATERIALS = r"K:\Programming\GitHub\tiny-alchemist\scripts\lapgc\lvimport_materials.json"
OUTPUT_PATH_MATERIALS_TEXT = r"K:\Programming\GitHub\tiny-alchemist\scripts\lapgc\working_materials.txt"
OUTPUT_PATH_MATERIAL_STRINGS = r"K:\Programming\GitHub\tiny-alchemist\scripts\lapgc\material_strings.txt"

def unminecraftize(s: str) -> str:
    if s.startswith("minecraft:"):
        return s[10:]
    return s

materials = [];
with open(LIST_PATH, 'r', encoding='utf-8') as f:
    materials = [unminecraftize(e[:-1]) for e in f.readlines()]
    
print("Getting material data...", end="")
textures = []
workingmaterials = [];
workingmaterialstxt = [];
material_strings = []
for material in materials:
    if material == "air":
        continue
    # print(f"\rGetting {material}...                        ", end="")
    try:
        modeldata = {};
        with open(os.path.join(MODELS_PATH, "item", f"{material}.json"), 'r', encoding='utf-8') as f:
            modeldata = json.load(f)
        texture = ""
        for i in range(10):
            if 'textures' in modeldata:
                texture = list(modeldata['textures'].values())[-1]
                if 'layer1' in modeldata['textures']:
                    texture = modeldata['textures']['layer1']
            elif 'parent' in modeldata:
                # print(os.path.join(MODELS_PATH, f"{modeldata['parent'][10:]}.json"))
                with open(os.path.join(MODELS_PATH, f"{unminecraftize(modeldata['parent'])}.json"), 'r', encoding='utf-8') as f:
                    modeldata = json.load(f)
        texture = unminecraftize(texture)
        print(f"\rTexture: {texture}                             ", end="")
        texture_data = textureToGzip(os.path.join(TEXTURES_PATH, f"{texture}.png"));
        textures.append(texture_data)
        workingmaterials.append(gzip_and_base64_encode(bytearray(material.encode('utf-8'))))
        workingmaterialstxt.append(material)
        # shutil.copyfile(os.path.join(TEXTURES_PATH, f"{texture}.png"), os.path.join(OUTPUT_PATH, f"{material}.png"))
    except Exception as e:
        print(f"\rCouldn't find texture for {material}", end="")
print(f"\rDone.                                                          ", end="")
for material_chunk in chunk_list(workingmaterialstxt, 500):
    material_strings.append(gzip_and_base64_encode(bytearray((','.join(material_chunk)).encode('utf-8'))))
    
with open(OUTPUT_PATH_MATERIALS, 'w') as f:
    json.dump(workingmaterials, f, indent=4)
with open(OUTPUT_PATH_MATERIALS_TEXT, 'w') as f:
    f.write('\n'.join(workingmaterialstxt))
with open(OUTPUT_PATH_MATERIAL_STRINGS, 'w') as f:
    f.write('\n'.join(material_strings))
with open(OUTPUT_PATH_TEXTURES, 'w') as f:
    json.dump(textures, f, indent=4)