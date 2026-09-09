import base64
import io
import os
import zipfile


def create_self_extractor(source_dir, output_py_path="self_extractor.py"):
    """Compresses a directory, encodes it, and writes a self-extracting Python script."""
    source_dir = os.path.abspath(source_dir)

    # 1. Create the ZIP archive in memory using LZMA
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(
        zip_buffer, "w", compression=zipfile.ZIP_LZMA
    ) as zipf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, start=source_dir)
                zipf.write(file_path, arcname=arcname)

    # 2. Base64 encode the binary ZIP data
    zip_buffer.seek(0)
    b64_data = base64.b64encode(zip_buffer.read()).decode("utf-8")

    # 3. Generate the self-extracting python code template
    script_content = f'''import base64
import io
import zipfile
import os

# The entire LZMA-compressed ZIP payload stored as a string variable
ZIP_PAYLOAD = "{b64_data}"

def extract_payload(extract_to_dir="."):
    """Decodes the embedded payload and extracts it to the target directory."""
    print("Decoding and extracting files...")
    
    # Reconstruct the binary ZIP from the Base64 string
    zip_bytes = base64.b64decode(ZIP_PAYLOAD)
    zip_buffer = io.BytesIO(zip_bytes)
    
    # Extract the files
    with zipfile.ZipFile(zip_buffer, "r") as zipf:
        zipf.extractall(path=extract_to_dir)
    
    print(f"Successfully extracted all files to: {{os.path.abspath(extract_to_dir)}}")

if __name__ == "__main__":
    extract_payload()
'''

    # 4. Write the final self-extracting script to disk
    with open(output_py_path, "w", encoding="utf-8") as f:
        f.write(script_content)

    print(f"Generated standalone self-extractor file: {output_py_path}")


if __name__ == "__main__":
    # Compresses everything in the current directory ('.') into 'self_extractor.py'
    create_self_extractor(".", "self_extractor.py")
