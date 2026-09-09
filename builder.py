import base64
import io
import os
import zipfile


def create_self_extractor(
    source_dir,
    template_path="input.py",
    output_py_path="self_extractor.py",
):
    """Compresses a directory, reads a text template, and outputs a self-extracting script."""
    source_dir = os.path.abspath(source_dir)

    # 1. Verify the template file exists before proceeding
    if not os.path.exists(template_path):
        raise FileNotFoundError(
            f"Could not find template file at: {template_path}. Please create it first."
        )

    # 2. Create the ZIP archive in memory using LZMA
    print("Compressing directory data...")
    zip_buffer = io.BytesIO()
    excluded_dirs = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
}

    excluded_files = {
        os.path.basename(output_py_path),
        os.path.basename(template_path),
    }

    with zipfile.ZipFile(
        zip_buffer, "w", compression=zipfile.ZIP_LZMA
    ) as zipf:

        for root, dirs, files in os.walk(source_dir):

            # Prevent os.walk from entering these directories
            dirs[:] = [
                d for d in dirs
                if d not in excluded_dirs
            ]

            for file in files:
                if file in excluded_files:
                    continue

                file_path = os.path.join(root, file)
                arcname = os.path.relpath(
                    file_path,
                    start=source_dir
                )

                zipf.write(file_path, arcname=arcname)


    # 3. Base64 encode the binary ZIP data
    zip_buffer.seek(0)
    b64_data = base64.b64encode(zip_buffer.read()).decode("utf-8")

    # 4. Read the standalone template file
    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()

    # 5. Inject the base64 string into the template placeholder
    final_script = template_content.replace("{{PAYLOAD}}", b64_data)

    # 6. Write the final executable file to disk
    with open(output_py_path, "w", encoding="utf-8") as f:
        f.write(final_script)

    print(f"Generated standalone self-extractor file: {output_py_path}")


if __name__ == "__main__":
    # Compresses everything in the current directory ('.') into 'self_extractor.py'
    create_self_extractor(".", "input.py", "self_extractor.py")
