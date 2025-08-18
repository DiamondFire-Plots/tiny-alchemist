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
import colorsys
import shutil

REPO_PATH = r"K:\Programming\GitHub\tiny-alchemist";
LOG_PATH = r"C:\Users\User\AppData\Roaming\PrismLauncher\instances\DiamondFire\minecraft\logs\latest.log"
SEARCH = "$$$ start "
RPACK_PATH_FULL = r"C:\Users\User\AppData\Roaming\PrismLauncher\instances\DiamondFire\minecraft\resourcepacks\Tiny Alchemist";
RPACK_PATH = os.path.join(RPACK_PATH_FULL, r"assets\minecraft");
ZIP_RPACK_PATH = r"K:\Programming\GitHub\tiny-alchemist\rpack\LAPGC.zip";
MODELS_PATH = r"models\custom\elements"
TEXTURES_PATH = r"textures\custom\elements"
ELEMENT_MODEL_PATHES = [r"models\item\filled_map.json", r"models\item\flint.json"]
MODEL_OVERRIDES = {
    995: ["item/potion", "item/potion_overlay"],
    854: ["item/leather_helmet_overlay", "item/leather_helmet"],
    855: ["item/leather_chestplate_overlay", "item/leather_chestplate"],
    856: ["item/leather_leggings_overlay", "item/leather_leggings"],
    857: ["item/leather_boots_overlay", "item/leather_boots"],
    1157: ["item/tipped_arrow_base", "item/tipped_arrow_head"],
    979: "item/filled_map",
    1110: "item/firework_star"
    
}

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

def rgba_to_hsba(rgba):
    r, g, b, a = rgba
    r, g, b = [x / 255.0 for x in (r, g, b)]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    return (
        int(h * 360),
        int(s * 100),
        int(v * 100),
        int(255)
    )

def hsba_to_rgba(hsba):
    h, s, v, a = hsba
    h, s, v = h / 360.0, s / 100.0, v / 100.0
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (
        int(r * 255),
        int(g * 255),
        int(b * 255),
        int(255)
    )


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
    if os.path.exists(models_path):
        shutil.rmtree(models_path)
    os.makedirs(models_path);
    if os.path.exists(textures_path):
        shutil.rmtree(textures_path)
    os.makedirs(textures_path);
    overrides = [];
    empty_textures=[];
    added = 0;
    for ri, c in enumerate(chatcut):
        i = ri + 1; # that's the DF index of the item
        buffer = decode_gzip_base64(c);
        palette = [[0,0,0,0]];
        pixels_overlay = [];
        pixels = [];
        overlay_empty = True
        
        for pi in range(32):
            color = [int(buffer[pi*3]), int(buffer[pi*3+1]), int(buffer[pi*3+2]), 255];
            add_hsb = rgba_to_hsba(tuple(color))
            palette.append(color)
            
        saturation = 0
        saturation_max = 0
        opaque = 0
        for ti in range(256):
            add_color = palette[buffer[ti+96]]
            if add_color[3] == 0:
                continue
            add_hsb = rgba_to_hsba(tuple(add_color))
            saturation += add_hsb[1]
            saturation_max = max(saturation_max, add_hsb[1])
            opaque += 1

        if opaque == 0:
            empty_textures.append(ri)
        else:
            saturation = float(saturation) / float(opaque)
            
        for ti in range(256):
            add_color = palette[buffer[ti+96]]
            if add_color[3] == 0:
                pixels_overlay.append([0,0,0,0])
                pixels.append([0,0,0,0])
                continue
            add_hsb = rgba_to_hsba(tuple(add_color))
            if add_hsb[1] <= 10 and saturation_max > 30 and saturation > 10: #saturation = 0
                pixels.append(add_color)
                pixels_overlay.append([0,0,0,0])
            else:
                add_hsb_list = list(add_hsb)
                add_hsb_list[1] = 0
                add_hsb = tuple(add_hsb_list)
                pixels_overlay.append(list(hsba_to_rgba(add_hsb)))
                overlay_empty = False
                pixels.append([0,0,0,0])
        if not os.path.exists(os.path.join(textures_path, f"{i}.png")):
            added += 1;
        
        if i not in MODEL_OVERRIDES:
            with open(os.path.join(models_path, f"{i}.json"), 'w', encoding='utf-8') as f:
                json.dump({
                            "parent": "minecraft:item/generated",
                            "textures": {
                            "layer0": f"minecraft:custom/elements/{i}",
                            "layer1": "minecraft:custom/other/empty" if overlay_empty else f"minecraft:custom/elements/{i}_overlay"
                            }
                        }, f, indent=4)
            
            save_rgba_palette_as_png(pixels, os.path.join(textures_path, f"{i}.png"))
            if not overlay_empty:
                save_rgba_palette_as_png(pixels_overlay, os.path.join(textures_path, f"{i}_overlay.png"))
            
            overrides.append({ "predicate": { "custom_model_data": i  }, "model": f"custom/elements/{i}" })
        else:
            if isinstance(MODEL_OVERRIDES[i], list):
                with open(os.path.join(models_path, f"{i}.json"), 'w', encoding='utf-8') as f:
                    json.dump({ "parent": "minecraft:item/generated", "textures": { "layer0": MODEL_OVERRIDES[i][0], "layer1": MODEL_OVERRIDES[i][1] }}, f, indent=4)
                overrides.append({ "predicate": { "custom_model_data": i  }, "model": f"custom/elements/{i}" })
            else:
                overrides.append({ "predicate": { "custom_model_data": i  }, "model": MODEL_OVERRIDES[i] })
            
        
        print(f"\rFinished element {i}!", end="")
    overrides.append({ "predicate": { "custom_model_data": len(overrides)+1  }, "model": f"custom/other/loading_element" })
    for path in ELEMENT_MODEL_PATHES:
        obj = {};
        with open(os.path.join(RPACK_PATH, path), 'r', encoding='utf-8') as f:
            obj = json.load(f);
        obj['overrides'] = overrides;
        with open(os.path.join(RPACK_PATH, path), 'w', encoding='utf-8') as f:
            json.dump(obj, f, indent=4)
    print(f"\rFinished generating all elements.");
    print(f"Empty Textures: {', '.join([str(e) for e in empty_textures])}")
    print(f"Zipping...")
    zip_folder(RPACK_PATH_FULL, ZIP_RPACK_PATH)
    print("Finished zipping!")
    message = f"Auto-update ({int(time.time())})";
    if added > 0:
        message += f" - added {added} element textures."
    should = input("Commit? 1 for yes")
    if should == "1":
        print("Committing...");
        auto_commit_and_push(REPO_PATH, message)
        print("Committed!");
        
main();