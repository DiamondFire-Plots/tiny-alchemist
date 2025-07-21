import json
import os
import sys
import base64
import gzip
from io import BytesIO
from PIL import Image
import zipfile
import subprocess
import time

REPO_PATH = r"K:\Programming\GitHub\tiny-alchemist";
LOG_PATH = r"C:\Users\User\AppData\Roaming\PrismLauncher\instances\Simply Optimized(1)\minecraft\logs\latest.log"
SEARCH = "$$$ start "
RPACK_PATH_FULL = r"C:\Users\User\AppData\Roaming\PrismLauncher\instances\Simply Optimized(1)\minecraft\resourcepacks\Tiny Alchemist";
RPACK_PATH = os.path.join(RPACK_PATH_FULL, r"assets\minecraft");
ZIP_RPACK_PATH = r"K:\Programming\GitHub\tiny-alchemist\rpack\Tiny Alchemist.zip";
MODELS_PATH = r"models\custom\elements"
TEXTURES_PATH = r"textures\custom\elements"
ELEMENT_MODEL_PATHES = [r"models\item\coal.json", r"models\item\flint.json"]

def auto_commit_and_push(repo_dir: str, commit_message: str):
    if not os.path.isdir(repo_dir):
        raise ValueError(f"{repo_dir} is not a valid directory")
    def run_git_cmd(args):
        result = subprocess.run(['git'] + args, cwd=repo_dir, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Git command failed: {' '.join(args)}\n{result.stderr.strip()}")
        return result.stdout.strip()
    run_git_cmd(['rev-parse', '--is-inside-work-tree'])
    run_git_cmd(['add', '--all'])
    run_git_cmd(['commit', '-m', commit_message])
    run_git_cmd(['push'])

def save_rgba_palette_as_png(colors: list, path: str):
    img = Image.new('RGBA', (16, 16))
    img.putdata([tuple(c) for c in colors])
    img.save(path, format='PNG')

def decode_gzip_base64(input_str: str) -> bytes:
    compressed_data = base64.b64decode(input_str)
    with gzip.GzipFile(fileobj=BytesIO(compressed_data)) as f:
        original_bytes = f.read()
    return original_bytes

def zip_folder(folder_path: str, zip_path: str):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, start=folder_path)
                zipf.write(full_path, arcname=relative_path)


chat = [];
def main():
    global chat
    print("Reading Log File...", end="")
    chat = [];
    with open(LOG_PATH, 'r', encoding='utf-8') as f:
        fr = f.readlines()
        chat = [j[29:] for j in list(filter(lambda h: h.startswith("[Render thread/INFO]: [CHAT] "), [e[11:-1] for e in fr]))]
        

    find = 0;
    amt = 0;
    print(f"\rRead Log File, Chat Length: {len(chat)}", end="")
    chatcut = [];
    for gi, g in enumerate(chat):
        if g.startswith(SEARCH):
            find = gi
            amt = int(g.replace(SEARCH, ""));
    chatcut = chat[find+1:find+1+amt]
    print(f"\rCreating {len(chatcut)} textures...                     ");
    models_path = os.path.join(RPACK_PATH, MODELS_PATH);
    textures_path = os.path.join(RPACK_PATH, TEXTURES_PATH);
    overrides = [];
    added = 0;
    for ri, c in enumerate(chatcut):
        i = ri + 1; # that's the DF index of the item
        with open(os.path.join(models_path, f"{i}.json"), 'w', encoding='utf-8') as f:
            json.dump({
                        "parent": "minecraft:item/generated",
                        "textures": {
                        "layer0": f"minecraft:custom/elements/{i}"
                        }
                    }, f, indent=4)
        buffer = decode_gzip_base64(c);
        palette = [[0,0,0,0]];
        pixels = [];
        for pi in range(32):
            color = [int(buffer[pi*3]), int(buffer[pi*3+1]), int(buffer[pi*3+2]), 255];
            palette.append(color)
        for ti in range(256):
            pixels.append(palette[buffer[ti+96]])
        if not os.path.exists(os.path.join(textures_path, f"{i}.png")):
            added += 1;
        save_rgba_palette_as_png(pixels, os.path.join(textures_path, f"{i}.png"))
            
            
            
        overrides.append({ "predicate": { "custom_model_data": i  }, "model": f"custom/elements/{i}" })
        
        print(f"\rFinished element {i}!", end="")
    overrides.append({ "predicate": { "custom_model_data": len(overrides)+1  }, "model": f"custom/other/loading_element" })
    for path in ELEMENT_MODEL_PATHES:
        obj = {};
        with open(os.path.join(RPACK_PATH, path), 'r', encoding='utf-8') as f:
            obj = json.load(f);
        obj['overrides'] = overrides;
        with open(os.path.join(RPACK_PATH, path), 'w', encoding='utf-8') as f:
            json.dump(obj, f, indent=4)
    print(f"\rFinished generating all elements, zipping...");
    zip_folder(RPACK_PATH_FULL, ZIP_RPACK_PATH)
    print("Finished zipping, committing...")
    auto_commit_and_push(REPO_PATH, f"Auto-update ({int(time.time())}) - added {added} element textures.")
    print("Committed!");
        
main();