import base64
import io
import zipfile
import os

# The entire LZMA-compressed ZIP payload stored as a string variable
ZIP_PAYLOAD = "{PAYLOAD}"

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
    os.subprocess.run(["python3", "main.py"]) 
    # Run the main.py script after extraction. Adjust the command as needed for your environment.