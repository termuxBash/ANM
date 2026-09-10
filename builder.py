import base64
import io
import os
import zipfile


def create_self_extractor(
    source_dir,
    selected_files,
    template_path="input.py",
    output_py_path="self_extractor.py",
):
    """Compress only selected files into a self-extracting script."""
    source_dir = os.path.abspath(source_dir)

    if not os.path.exists(template_path):
        raise FileNotFoundError(
            f"Could not find template file at: {template_path}"
        )

    print("Compressing selected files...")

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(
        zip_buffer, "w", compression=zipfile.ZIP_LZMA
    ) as zipf:

        for relative_path in selected_files:
            file_path = os.path.join(source_dir, relative_path)

            if not os.path.isfile(file_path):
                raise FileNotFoundError(
                    f"Selected file does not exist: {file_path}"
                )

            # Keep the relative path inside the ZIP
            zipf.write(
                file_path,
                arcname=relative_path
            )

    # Base64 encode ZIP
    zip_buffer.seek(0)
    b64_data = base64.b64encode(
        zip_buffer.read()
    ).decode("utf-8")

    # Read template
    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()

    # Inject payload
    final_script = template_content.replace(
        "{{PAYLOAD}}",
        b64_data
    )

    # Write output
    with open(output_py_path, "w", encoding="utf-8") as f:
        f.write(final_script)

    print(
        f"Generated standalone self-extractor file: "
        f"{output_py_path}"
    )


if __name__ == "__main__":
    create_self_extractor(
        ".",
        selected_files=[
            "data.db.enc",
            "input.py",
            "app.py",
            "extractor.py",
            "main.py",
            "EncryptedDB.py",
            "builder.py",
        ],
        template_path="input.py",
        output_py_path="self_extractor.py",
    )
