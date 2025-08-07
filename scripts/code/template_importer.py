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
print(f"Pick file path of template.json file.")
Tk().withdraw()
FILE_PATH = askopenfilename()
TEMPLATES = {}
FORCE_HIDDEN = True
HIDDEN_STATE = True
COMPACT = True
with open(FILE_PATH, 'r', encoding='utf-8') as f:
    TEMPLATES = json.load(f)
    
def filter(type: str, name: str, data: str) -> str:
    return (type!="event") and (not name.startswith("//")) and ("/" in name) and (not name.startswith("#")) and (not name.lower().startswith("e/"))

FILTER = filter

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


ws.send(f'place {'compact' if COMPACT else 'swap'}');
print("Importing...")
total_templates = []
total_templates.extend([('function',e,k) for e,k in TEMPLATES['functions'].items()])
total_templates.extend([('process',e,k) for e,k in TEMPLATES['processes'].items()])
total_templates.extend([('event',e,k) for e,k in TEMPLATES['events'].items()])
counts = {'function': 0, 'process': 0, 'event': 0}
for template_type, template_name, template_data in total_templates:
    sleep(0.02)
    # print(template_type, template_name, template_data)
    if FORCE_HIDDEN and template_type != 'event':
        parsed_template_data = json.loads(base64_and_gzip_decode(template_data))
        parsed_template_data['blocks'][0]['args']['items'][-1]['item']['data']['option'] = 'True' if HIDDEN_STATE else 'False'
        template_data = gzip_and_base64_encode(bytearray(json.dumps(parsed_template_data).encode('utf-8')))
    if not FILTER(template_type, template_name, template_data):
        continue
    ws.send('place ' + template_data);  
    counts[template_type] += 1
    print(f"\rImported {template_name}...                                        ", end="")
sleep(0.5)
ws.send('place go');  
print(f"\rDone Importing!                                        ", end="\n")
print(f"Out of {len(TEMPLATES['functions'])} functions, {len(TEMPLATES['processes'])} processes and {len(TEMPLATES['events'])} events,")
print(f"imported {counts['function']} functions, {counts['process']} processes and {counts['event']} events.")
