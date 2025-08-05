import json
import os
import gzip
import base64
import io
import shutil
from PIL import Image

LOG_PATH = r"C:\Users\User\AppData\Roaming\PrismLauncher\instances\Simply Optimized(1)\minecraft\logs\latest.log"
IDENTIFIER = "Ԕ֐ļЕΚӰԾԾȒɁ"
OUTPUT_PATH = r"K:\Programming\GitHub\tiny-alchemist\scripts\backup\output"
ATLAS_BLOCK_SIZE = 32



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

def save_rgba_as_png(colors: list, size: int, path: str):
    img = Image.new('RGBA', (size, size))
    img.putdata([tuple(c) for c in colors])
    img.save(path, format='PNG')
    
    
def chunk_list(data, block_size):
    return [data[i:i+block_size] for i in range(0, len(data), block_size)]

def key_value():
    global chat, pointer, chatDates
    name = get_next_message()
    print(name)
    length = int(get_next_message())
    timeget = chatDates[pointer].replace(":", ".")
    final = {}
    print(f"Backing up Key-Value database '{name}' of of length {length}...")
    for i in range(length):
        key = get_next_message()
        value = get_next_message()
        final[key] = value
    path = os.path.join(OUTPUT_PATH, f"kvbackup_{name}_{timeget}.json")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(final, f, indent=4)
    print(f"Backed up.")
    
def key_values():
    global chat, pointer, chatDates
    name = get_next_message()
    print(name)
    length = int(get_next_message())
    timeget = chatDates[pointer].replace(":", ".")
    final = {}
    print(f"Backing up Key-Values database '{name}' of of length {length}...")
    for i in range(length):
        key = get_next_message()
        values_length = int(get_next_message())
        values = []
        for i in range(values_length):
            values.append(get_next_message())
        final[key] = values
    path = os.path.join(OUTPUT_PATH, f"kvsbackup_{name}_{timeget}.json")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(final, f, indent=4)
    print(f"Backed up.")
    
def list_value():
    global chat, pointer, chatDates
    name = get_next_message()
    print(name)
    length = int(get_next_message())
    timeget = chatDates[pointer].replace(":", ".")
    final = []
    print(f"Backing up List-Value database '{name}' of of length {length}...")
    for i in range(length):
        value = get_next_message()
        final.append(value)
    path = os.path.join(OUTPUT_PATH, f"lvbackup_{name}_{timeget}.json")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(final, f, indent=4)
    print(f"Backed up.")
    
def list_object():
    global chat, pointer, chatDates
    name = get_next_message()
    print(name)
    length = int(get_next_message())
    timeget = chatDates[pointer].replace(":", ".")
    final = []
    print(f"Backing up List-Object database '{name}' of of length {length}...")
    for i in range(length):
        value = json.loads(base64_and_gzip_decode(get_next_message()))
        final.append(value)
    path = os.path.join(OUTPUT_PATH, f"lobackup_{name}_{timeget}.json")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(final, f, indent=4)
    print(f"Backed up.")
    
def list_values():
    global chat, pointer, chatDates
    name = get_next_message()
    print(name)
    length = int(get_next_message())
    # length = 100
    timeget = chatDates[pointer].replace(":", ".")
    final = []
    print(f"Backing up List-Values database '{name}' of of length {length}...")
    for i in range(length):
        values_length = int(get_next_message())
        values = []
        for i in range(values_length):
            val = get_next_message()
            if val.startswith("<white></white>"):
                val = val[15:]
            values.append(val)
        final.append(values)
    path = os.path.join(OUTPUT_PATH, f"lvsbackup_{name}_{timeget}.json")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(final, f, indent=4)
    print(f"Backed up.")
    
def texture_atlas():
    global chat, pointer, chatDates
    name = get_next_message()
    print(name)
    length = int(get_next_message())
    timeget = chatDates[pointer].replace(":", ".")
    buffers = []
    print(f"Backing up Texture Atlas database '{name}' of of length {length}...")
    for i in range(length):
        value = base64_and_gzip_decode(get_next_message())
        buffers.append(value)
    folder_path = os.path.join(OUTPUT_PATH, f"tabackup_{name}_{timeget}")
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
    os.makedirs(folder_path);
    buffer_chunks = chunk_list(buffers, ATLAS_BLOCK_SIZE*ATLAS_BLOCK_SIZE);
    index_object = {
        "length": length,
        "size": ATLAS_BLOCK_SIZE,
        "use_resized": False, 
        "atlases": []
    }
    si = 1
    for chunk in buffer_chunks:
        atlas_name = f"{si}-{si+len(chunk)-1}.png"
        if len(chunk) == 1:
            atlas_name = f"{si}.png"
        index_object['atlases'].append(atlas_name);
        pixels = [[0,0,0,0]] * ATLAS_BLOCK_SIZE * ATLAS_BLOCK_SIZE * 16 * 16;
        pixels_8x8 = [[0,0,0,0]] * ATLAS_BLOCK_SIZE * ATLAS_BLOCK_SIZE * 8 * 8;
        pixels_4x4 = [[0,0,0,0]] * ATLAS_BLOCK_SIZE * ATLAS_BLOCK_SIZE * 4 * 4;
        for bi, buffer in enumerate(chunk):
            si += 1
            palette = [[0,0,0,0]];
            for pi in range(32):
                color = [int(buffer[pi*3]), int(buffer[pi*3+1]), int(buffer[pi*3+2]), 255];
                palette.append(color)
            for ti in range(256):
                x = (ti % 16) + ((bi % ATLAS_BLOCK_SIZE) * 16)
                y = (ti // 16) + ((bi // int(ATLAS_BLOCK_SIZE)) * 16)
                pixels[x + (y*ATLAS_BLOCK_SIZE*16)] = palette[buffer[ti+96]]
            for ti in range(64):
                x = (ti % 8) + ((bi % ATLAS_BLOCK_SIZE) * 8)
                y = (ti // 8) + ((bi // int(ATLAS_BLOCK_SIZE)) * 8)
                pixels_8x8[x + (y*ATLAS_BLOCK_SIZE*8)] = palette[buffer[ti+96+256]]
            for ti in range(16):
                x = (ti % 4) + ((bi % ATLAS_BLOCK_SIZE) * 4)
                y = (ti // 4) + ((bi // int(ATLAS_BLOCK_SIZE)) * 4)
                pixels_4x4[x + (y*ATLAS_BLOCK_SIZE*4)] = palette[buffer[ti+96+256+64]]
        save_rgba_as_png(pixels, ATLAS_BLOCK_SIZE * 16, os.path.join(folder_path, atlas_name))
        save_rgba_as_png(pixels_8x8, ATLAS_BLOCK_SIZE * 8, os.path.join(folder_path, "small_"+atlas_name))
        save_rgba_as_png(pixels_4x4, ATLAS_BLOCK_SIZE * 4, os.path.join(folder_path, "tiny_"+atlas_name))
                
    with open(os.path.join(folder_path, f".index"), 'w', encoding='utf-8') as f:
        json.dump(index_object, f, indent=4)
    print(f"Backed up.")
    
def ignore():
    global chat, pointer, chatDates
    print('hey');

COMMANDS = {
    'KeyValue': key_value,
    'KeyValues': key_values,
    'ListValue': list_value,
    'ListValues': list_values,
    'ListObject': list_object,
    'TextureAtlas': texture_atlas,
    'Ignore': ignore
}

chat = []
chatDates = []
pointer = 0

def main():
    global chat, pointer, chatDates
    print("Reading Log File...")
    chat = [];
    with open(LOG_PATH, 'r', encoding='utf-8') as f:
        fr = f.readlines()
        chat = [j[29:] for j in list(filter(lambda h: h.startswith("[Render thread/INFO]: [CHAT] "), [e[11:-1] for e in fr]))]
        chatDates = [e[1:9] for e in fr]
        

    print(f"Read Log File, Chat Length: {len(chat)}")
    pointer = 0
    newpointer = 0;
    while True:
        current_message = get_next_message_raw()
        if current_message == None:
            break
        if current_message.startswith(f"{IDENTIFIER} Ignore"):
            newpointer = pointer;
    pointer = newpointer;
    while True:
        current_message = get_next_message_raw()
        if current_message == None:
            break
        if current_message.startswith(f"{IDENTIFIER} "):
            current_command = current_message[len(IDENTIFIER)+1:]
            print(f"Starting Command: {current_command}")
            try:
                COMMANDS[current_command]()
            except Exception as e:
                print(f"Failed command due to {e}.")
            
        
def get_next_message_raw():
    global chat, pointer
    if pointer >= len(chat):
        return None
    current_message = chat[pointer]
    pointer += 1
    return current_message
        
def get_next_message():
    message = get_next_message_raw()
    if message.startswith("1"):
        return message[1:]
    if message.startswith("0"):
        return message[1:] + get_next_message()
    
    
    

        
main()