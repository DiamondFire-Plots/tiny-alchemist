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


OUTPUT_PATH = r"K:\Programming\GitHub\tiny-alchemist\scripts\code\templates.json"
FILE_PATHES = []
print(f"Pick all file pathes of templates.")
while True:
    file_path = askopenfilename()
    if not (".dfplot" in os.path.basename(file_path)):
        break
    print(f"Added {file_path}.")
    FILE_PATHES.append(file_path)

TEMPLATES = {'functions': {}, 'events': {}, 'processes': {}}

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
    

seen_datas = set()
for file_path in FILE_PATHES:
    template_datas = []
    with open(file_path, 'r', encoding='utf-8') as f:
        template_datas = f.read().replace("\r", "").split("\n")
    for template_data in template_datas:
        if not is_valid_gzip_base64_string(template_data):
            continue
        if template_data in seen_datas:
            continue
        seen_datas.add(template_data)
        template = json.loads(base64_and_gzip_decode(template_data))
        root_block = template['blocks'][0]
        match root_block['block']:
            case 'func':
                while (root_block['data'] in TEMPLATES['functions']):
                    root_block['data'] = "#" + root_block['data']
                TEMPLATES['functions'][root_block['data']] = template_data
            case 'process':
                while (root_block['data'] in TEMPLATES['processes']):
                    root_block['data'] = "#" + root_block['data']
                TEMPLATES['processes'][root_block['data']] = template_data
            case 'event' | 'entity_event':
                while (root_block['action'] in TEMPLATES['events']):
                    root_block['action'] = "#" + root_block['action']
                TEMPLATES['events'][root_block['action']] = template_data

print(f"Saved {len(TEMPLATES['functions'])} functions, {len(TEMPLATES['processes'])} processes and {len(TEMPLATES['events'])} events.")
with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(TEMPLATES, f, indent=4)