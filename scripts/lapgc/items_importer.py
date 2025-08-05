import json
import os
import gzip
import base64
import io
import shutil
from PIL import Image
import Levenshtein
from datetime import datetime, timezone

import re
import string
import random

def replace_last_5_with_random(s):
    if len(s) < 5:
        raise ValueError("String must be at least 5 characters long.")
    random_suffix = ''.join(random.choices(string.ascii_lowercase, k=5))
    return s[:-5] + random_suffix

def visible_str(s):
    cleaned = re.sub(r"</?[^>]+>", "", s)
    return cleaned.strip()

def clean_string(s):
    return re.sub(r'[^a-z]', '', s.lower())

def strip_str(s):
    return clean_string(visible_str(s))

def to_utc_timestamp(s):
    dt = datetime.strptime(s, "%Y/%m/%d %H:%M:%S")
    return dt.replace(tzinfo=timezone.utc).timestamp()

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

def list_to_bitset_bytearray(numbers):
    if not numbers:
        return bytearray()
    max_bit = max(numbers)
    bitset = [0] * ((max_bit + 7) // 8)
    for n in numbers:
        byte_index = (n - 1) // 8
        bit_index = (n - 1) % 8
        bitset[byte_index] |= 1 << bit_index
    while bitset and bitset[-1] == 0:
        bitset.pop()
    return bytearray(bitset)

def trim_trailing_lore(entries):
    def is_metadata_line(s):
        return any(
            s.strip().startswith(f"<dark_gray>{key}")
            for key in ["By:", "ID:", "Ingredient Level:", "Date:"]
        ) or s.strip() == "<gray>"
    newEntries = []
    for entry in entries:
        if not is_metadata_line(entry):
            newEntries.append(entry)
    if len(newEntries) == 1:
        if newEntries[0] == "":
            newEntries = []
    return newEntries

OUTPUT_PATH = r"K:\Programming\GitHub\tiny-alchemist\scripts\lapgc\lvimport_items.json"
OUTPUT_COLL_PATH = r"K:\Programming\GitHub\tiny-alchemist\scripts\lapgc\lvimport_collection.json"
PLAYERS_PATH = r"K:\Programming\GitHub\tiny-alchemist\scripts\lapgc\lvimport_players.json"
COLORS_PATH = r"K:\Programming\GitHub\tiny-alchemist\scripts\lapgc\lvimport_colors.json"
DUMP_PATH = r"K:\Programming\Programs\DiamondFire Backup\output\oldandimportant\lvsbackup_LAPGC_3_21.29.32.json"
MATERIALS_PATH = r"K:\Programming\GitHub\tiny-alchemist\scripts\lapgc\working_materials.txt"
RELINK_UUIDS = {
    # "14225215-9da7-4f3d-8bf3-f154b66d86ad": "bd30206a-5de1-47d9-984c-3878a82d4640"
}


dump = [];
with open(DUMP_PATH, 'r', encoding='utf-8') as f:
    dump = json.load(f)
    
colors = [];
with open(COLORS_PATH, 'r', encoding='utf-8') as f:
    colors = json.load(f)
    
players = [];
uuids = []
player_dicts = []
with open(PLAYERS_PATH, 'r', encoding='utf-8') as f:
    players = [e.split(" ") for e in json.load(f)]
    uuids = [e[0] for e in players]
    player_dicts = [json.loads(base64_and_gzip_decode(e[2])) for e in players]
    
    
materials = [];
with open(MATERIALS_PATH, 'r', encoding='utf-8') as f:
    materials = [e.replace("\n", "") for e in f.readlines()]
    
output = []
collection = []
default_date = 1609606492
existing_names = {}
totalLens = []
maxx = 0
for id, unparsed in enumerate(dump):
    texture = 0
    try:
        texture = materials.index(unparsed[1])
    except ValueError:
        # Use Levenshtein distance to find the closest match
        closest = min(materials, key=lambda x: Levenshtein.distance(x, unparsed[1]))
        texture = materials.index(closest)
        print(f"Substituted '{unparsed[1]}' for '{materials[texture]}'")
    lore = []
    lorelength = 0
    pointer = 5
    for i in range(int(unparsed[4])):
        lore.append(unparsed[pointer])
        lorelength += len(unparsed[pointer])
        pointer += 1
    tags = {}
    for i in range(int(unparsed[pointer])):
        pointer += 2
        tags[unparsed[pointer-1]] = unparsed[pointer]
    flags = 0
    if unparsed[2] == "1":
        flags += 1
    author = 1
    recipe = [0,0]
    if 'ingredients' in tags:
        recipe = [int(e) for e in tags['ingredients'].split('-')]
        if tags['owner'] in RELINK_UUIDS:
            tags['owner'] = RELINK_UUIDS[tags['owner']]
        author = uuids.index(tags['owner'])+1
    date = default_date
    try:
        date = round(to_utc_timestamp(date.replace("<dark_gray>Date: </dark_gray><gray>", "")))
    except:
        pass
    unlocked = []
    di = 0
    
    while True:
        di += 1
        if f'data{di}' not in tags:
            break
        data = tags[f'data{di}']
        for i in range(5):
            data = data.replace("..", ".")
        data = data.strip(".").split(".")
        unlocked.extend([int(e) for e in data])
    unlocked.sort()
    for pid in unlocked:
        if 'i' not in player_dicts[pid-1]:
            player_dicts[pid-1]['i'] = 0
        player_dicts[pid-1]['i'] += 1
    itemcollection = gzip_and_base64_encode(list_to_bitset_bytearray(unlocked))
    collection.append(itemcollection)
    lore = trim_trailing_lore(lore)
    if lorelength > 3000:
        lore = ["Lore removed because it was too long."]
    rawname = unparsed[0]
    if len(rawname) > 400:
        # print(f"Cutting {rawname} because it was {len(rawname)} long!")
        rawname = rawname[0:400]
    lll = len(strip_str(rawname))
    if lll < 2:
        # print(f"Cutting {rawname} because it was {len(rawname)} long!")
        rawname = f"invalidname_{''.join(random.choices(string.ascii_lowercase, k=7))}_{rawname}"
    lll = len(strip_str(rawname))
    if lll > 55:
        rawname = visible_str(rawname)[0:45] + visible_str(rawname)[-10:]
    while True:
        if strip_str(rawname) not in existing_names:
            break
        # print(f"Changing {rawname} because it already exists, originally cut because it was {lll} long!")
        rawname = replace_last_5_with_random(rawname)
    existing_names[strip_str(rawname)] = id
    
    
    obj = {
        "flags": flags,
        'author': author,
        "texture": texture,
        "date": date,
        "recipe": recipe,
        "rawname": rawname,
        "lore": lore,
        # "tags": tags
    }
    if colors[id] != "#000000":
        obj['color'] = colors[id]
    
    maxx = max(maxx, len(gzip_and_base64_encode(bytearray(json.dumps(obj).encode('utf-8')))))
    maxx = max(maxx, len(bytearray(json.dumps(obj).encode('utf-8'))))
    # totalLens.append()
    
    output.append(obj)

for pid, pdict in enumerate(player_dicts):
    players[pid][2] = gzip_and_base64_encode(bytearray(json.dumps(pdict).encode('utf-8')))

with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=4)
    
with open(OUTPUT_COLL_PATH, 'w', encoding='utf-8') as f:
    json.dump(collection, f, indent=4)
    
with open(PLAYERS_PATH, 'w', encoding='utf-8') as f:
    json.dump([" ".join(e) for e in players], f, indent=4)
    
    
print(maxx)