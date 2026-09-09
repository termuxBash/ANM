import os
import zipfile


def lzma_zip_directory(source_dir, output_zip_path):
    """Compresses an entire directory into a ZIP file using LZMA compression."""
    # Ensure target directory exists
    source_dir = os.path.abspath(source_dir)

    # Open the zip file with LZMA compression enabled
    with zipfile.ZipFile(
        output_zip_path, "w", compression=zipfile.ZIP_LZMA
    ) as zipf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                # Get absolute path of the file
                file_path = os.path.join(root, file)

                # Create a relative path to preserve the folder structure inside the ZIP
                arcname = os.path.relpath(file_path, start=source_dir)

                # Add file to the archive
                zipf.write(file_path, arcname=arcname)
                print(f"Compressed: {arcname}")

def main():
    lzma_zip_directory('.', "temp.zip")
if __name__ == "__main__":
    main()