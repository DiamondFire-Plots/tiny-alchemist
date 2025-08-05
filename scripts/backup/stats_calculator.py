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

stats = []
items = []

print("Open Items File!")
ITEMS_FILE_PATH = askopenfilename(title="Open Items File")

with open(ITEMS_FILE_PATH, 'r', encoding='utf-8') as f:
    items = json.load(f)
    
print("Open Stats File!")
STATS_FILE_PATH = askopenfilename(title="Open Stats File")

if STATS_FILE_PATH == "":
    STATS_FILE_PATH = ITEMS_FILE_PATH[0:-5] + "_calculated_stats.json"
else:
    with open(STATS_FILE_PATH, 'r', encoding='utf-8') as f:
        stats = json.load(f)
    
if len(stats) < len(items):
    print("Open Collection File!")
    COLLECTION_FILE_PATH = askopenfilename(title="Open Collection File")
    collection = []
    with open(COLLECTION_FILE_PATH, 'r', encoding='utf-8') as f:
        collection = [base64_and_gzip_decode(e) for e in json.load(f)]
    for i in range(len(items) - len(stats)):
        stats.append({
            "complexity": 0,
            "isexact": 0,
            "favorites": 0,
            "unlocked": 0
        })
    for i, coll in enumerate(collection):
        stats[i]['unlocked'] = 0
        for count in coll:
            stats[i]['unlocked'] += count.bit_count()
    
# print(stats)
# print(items)
print("Loading...        ", end="")
bitsets = []
print("\rCalculating...        ", end="")
for ri, item in enumerate(items):
    i = ri + 1 # DF id
    bitset = 1 << ri
    if i > 2:
        for ing in item['recipe']:
            bitset |= bitsets[ing-1]
    bitsets.append(bitset)
    complexity = bitset.bit_count()
        
    # print(f"\rCalculating ID {i}...       ", end="")
        
    stats[ri]['complexity'] = complexity
    stats[ri]['isexact'] = 1
print("\rSaving...             ", end="")
    
with open(STATS_FILE_PATH, 'w', encoding='utf-8') as f:
    json.dump(stats, f, indent=4)
print("\rDone!              ", end="")