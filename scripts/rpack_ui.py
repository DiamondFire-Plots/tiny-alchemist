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
import shutil

REPO_PATH = r"K:\Programming\GitHub\tiny-alchemist";
LOG_PATH = r"C:\Users\User\AppData\Roaming\PrismLauncher\instances\DiamondFire\minecraft\logs\latest.log"
TEXT_PATH = r"K:\Programming\GitHub\tiny-alchemist\scripts\rpack_ui.txt"
SEARCH = "$$$ start "
RPACK_PATH_FULL = r"C:\Users\User\AppData\Roaming\PrismLauncher\instances\DiamondFire\minecraft\resourcepacks\Tiny Alchemist";
RPACK_PATH = os.path.join(RPACK_PATH_FULL, r"assets\minecraft");
ZIP_RPACK_PATH = r"K:\Programming\GitHub\tiny-alchemist\rpack\Tiny Alchemist.zip";
MODELS_PATH = r"models\custom\elements"
TEXTURES_PATH = r"textures\custom\elements"
ELEMENT_MODEL_PATHES = [r"models\item\filled_map.json", r"models\item\flint.json"]

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
    with open(TEXT_PATH, 'r', encoding='utf-8') as f:
        chat = f.readlines()

    

    should = input("Commit? 1 for yes")
    if should == "1":
        print("Committing...");
        auto_commit_and_push(REPO_PATH, message)
        print("Committed!");
        
main();