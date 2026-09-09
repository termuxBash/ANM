import os
import zipfile


def lzma_unzip_archive(zip_path, extract_to_dir):
    """Extracts an LZMA-compressed ZIP file into the specified target directory."""
    # Ensure the extraction destination exists
    if not os.path.exists(extract_to_dir):
        os.makedirs(extract_to_dir)
        print(f"Created destination directory: {extract_to_dir}")

    # Open and extract the zip archive
    with zipfile.ZipFile(zip_path, "r") as zipf:
        # Optional: Print file names as they extract
        for file_info in zipf.infolist():
            print(f"Extracting: {file_info.filename}")

        # Extract all contents
        zipf.extractall(path=extract_to_dir)


if __name__ == "__main__":
    # Example usage when running this script directly
    archive_to_extract = "./temp.zip"
    destination_folder = "./extracted_data"

    lzma_unzip_archive(archive_to_extract, destination_folder)
    print(f"\nSuccessfully extracted archive to: {destination_folder}")