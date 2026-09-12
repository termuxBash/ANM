import io
import os
import zipfile


MAIN_MODULE_TEMPLATE = '''import os
import subprocess
import sys
import zipfile

with zipfile.ZipFile(sys.argv[0], "r") as archive:
    archive.extractall(".")

main_py = os.path.abspath("main.py")

if not os.path.isfile(main_py):
    raise RuntimeError("main.py was not found after extraction.")

subprocess.run(
    [
        sys.executable,
        main_py,
        "--extractor-version",
        str({version}),
    ],
    check=False,
)
'''.encode("utf-8")


def create_self_extractor(
    source_dir,
    selected_files,
    version=1,
    output_py_path="self_extractor.py",
):
    """Compress selected files into a compact self-extracting script."""
    source_dir = os.path.abspath(source_dir)
    version = int(version)

    print(f"Compressing selected files (version {version})...")

    archive_buffer = io.BytesIO()

    with zipfile.ZipFile(
        archive_buffer,
        mode="w",
        compression=zipfile.ZIP_LZMA,
        compresslevel=9,
    ) as archive:

        archive.writestr(
            "__main__.py",
            MAIN_MODULE_TEMPLATE.decode("utf-8").format(
                version=version,
            ).encode("utf-8"),
            compress_type=zipfile.ZIP_STORED,
        )

        for relative_path in selected_files:
            file_path = os.path.join(
                source_dir,
                relative_path,
            )

            if not os.path.isfile(file_path):
                raise FileNotFoundError(
                    f"Selected file does not exist: {file_path}"
                )

            archive.write(
                file_path,
                arcname=relative_path,
            )

    with open(output_py_path, "wb") as f:
        f.write(archive_buffer.getvalue())

    os.chmod(output_py_path, 0o755)

    print(
        f"Generated standalone self-extractor "
        f"version {version}: {output_py_path}"
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
        version=1,
        output_py_path="self_extractor.py",
    )