import base64
import io
import lzma
import os
import tarfile


EXTRACTOR_TEMPLATE = '''import base64,io,lzma,subprocess,sys,tarfile
PAYLOAD="""{{PAYLOAD}}"""
with tarfile.open(fileobj=io.BytesIO(lzma.decompress(base64.b85decode(PAYLOAD))),mode="r:") as archive: archive.extractall(".")
subprocess.run([sys.executable,"main.py"])
'''


def create_self_extractor(
    source_dir,
    selected_files,
    template_path=None,
    output_py_path="self_extractor.py",
):
    """Compress selected files into a compact self-extracting script."""
    source_dir = os.path.abspath(source_dir)

    print("Compressing selected files...")

    archive_buffer = io.BytesIO()
    with tarfile.open(
        fileobj=archive_buffer, mode="w", format=tarfile.PAX_FORMAT
    ) as archive:
        for relative_path in selected_files:
            file_path = os.path.join(source_dir, relative_path)

            if not os.path.isfile(file_path):
                raise FileNotFoundError(
                    f"Selected file does not exist: {file_path}"
                )

            archive.add(file_path, arcname=relative_path, recursive=False)

    payload = base64.b85encode(
        lzma.compress(archive_buffer.getvalue(), preset=9)
    ).decode("ascii")

    if template_path is not None:
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Could not find template file at: {template_path}")
        with open(template_path, "r", encoding="utf-8") as f:
            template_content = f.read()
    else:
        template_content = EXTRACTOR_TEMPLATE

    final_script = template_content.replace(
        "{{PAYLOAD}}",
        payload
    )

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
            "app.py",
            "main.py",
            "builder.py",
        ],
        output_py_path="self_extractor.py",
    )
