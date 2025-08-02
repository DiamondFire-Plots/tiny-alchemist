import gzip
import base64
import json
import pyperclip
import io

def process_entry(encoded_str):
    # Step 1: base64 decode
    data = base64.b64decode(encoded_str)
    
    # Step 2: ungzip once
    with gzip.GzipFile(fileobj=io.BytesIO(data)) as gzf1:
        data = gzf1.read()
    
    # Step 3: ungzip again
    with gzip.GzipFile(fileobj=io.BytesIO(data)) as gzf2:
        data = gzf2.read()
    
    # Step 4: gzip again
    out = io.BytesIO()
    with gzip.GzipFile(fileobj=out, mode='wb') as gz_out:
        gz_out.write(data)
    compressed = out.getvalue()

    # Step 5: base64 encode
    return base64.b64encode(compressed).decode('utf-8')

def main():
    # Step 0: Read clipboard
    clipboard_data = pyperclip.paste()
    try:
        b64_list = json.loads(clipboard_data)
    except json.JSONDecodeError:
        print("Clipboard does not contain valid JSON.")
        return

    if not isinstance(b64_list, list):
        print("Clipboard does not contain a list.")
        return

    # Process and transform each item
    transformed = [process_entry(item) for item in b64_list]

    # Output back to clipboard
    pyperclip.copy(json.dumps(transformed, indent=4))
    print("Transformed list copied back to clipboard.")

if __name__ == "__main__":
    main()
