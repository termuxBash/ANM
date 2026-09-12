#!/usr/bin/env python3

import argparse
import base64
import hashlib
import json
import os
import secrets
import sqlite3
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Button, Footer, Header, Input, Label

from builder import create_self_extractor


BASE_DIR = Path(__file__).resolve().parent

ENCRYPTED_DB = BASE_DIR / "data.db.enc"
PLAINTEXT_DB = BASE_DIR / "data.db"
APP = BASE_DIR / "app.py"
EXTRACTED_FILES = (
    "__main__.py",
    "data.db.enc",
    "app.py",
    "main.py",
    "builder.py",
)

MAGIC = b"ENCDB01"
SALT_SIZE = 16
NONCE_SIZE = 12
KEY_SIZE = 32

WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzdizgIWCIuePy9MfodipQRPCU0C1Y5du7tX-v0jvsYxZq4FEpcloyb08rBroX1lQGV/exec"

def get_file_sha256(path: Path) -> str:
    if not path.is_file():
        return ""
    sha256 = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def check_remote_version() -> str:
    try:
        url = f"{WEB_APP_URL}?action=version"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as response:
            res = json.loads(response.read().decode("utf-8"))
            return str(res.get("version", "0"))
    except Exception:
        return "0"


def download_and_update_extractor(current_extractor_path: Path) -> bool:
    """Downloads the latest self_extractor.py from Google Drive and replaces the current one."""
    try:
        req = urllib.request.Request(WEB_APP_URL)
        with urllib.request.urlopen(req, timeout=30) as response:
            res = json.loads(response.read().decode("utf-8"))
            if res.get("status") == "success":
                encoded_data = res.get("data")
                file_bytes = base64.b64decode(encoded_data)
                
                current_extractor_path.write_bytes(file_bytes)
                current_extractor_path.chmod(0o755)
                return True
            else:
                print(f"Failed to download update: {res.get('message')}", file=sys.stderr)
    except Exception as exc:
        print(f"Error downloading self_extractor update: {exc}", file=sys.stderr)
    return False


def upload_self_extractor(file_path: Path, new_version: str):
    if not file_path.is_file():
        return
    raw_bytes = file_path.read_bytes()
    encoded_data = base64.b64encode(raw_bytes).decode("utf-8")

    data = urllib.parse.urlencode({
        "version": new_version,
        "data": encoded_data
    }).encode("utf-8")

    req = urllib.request.Request(WEB_APP_URL, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            res = json.loads(response.read().decode("utf-8"))
            if res.get("status") == "success":
                print("Successfully uploaded updated self_extractor.py to Google Drive.")
            else:
                print(f"Failed to upload: {res.get('message')}", file=sys.stderr)
    except Exception as exc:
        print(f"Error uploading self_extractor.py: {exc}", file=sys.stderr)


def derive_key(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=2**14,
        r=8,
        p=1,
        dklen=32,
    )


def decrypt_file(password: str):
    raw = ENCRYPTED_DB.read_bytes()

    if len(raw) < len(MAGIC) + SALT_SIZE + NONCE_SIZE + 16:
        raise ValueError("Encrypted file is corrupted.")

    if not raw.startswith(MAGIC):
        raise ValueError("Invalid encrypted database.")

    offset = len(MAGIC)

    salt = raw[offset:offset + SALT_SIZE]
    offset += SALT_SIZE

    nonce = raw[offset:offset + NONCE_SIZE]
    offset += NONCE_SIZE

    ciphertext = raw[offset:]

    key = derive_key(password, salt)

    plaintext = AESGCM(key).decrypt(
        nonce,
        ciphertext,
        MAGIC,
    )

    temp = PLAINTEXT_DB.with_name("data.db.tmp")

    try:
        with temp.open("wb") as f:
            f.write(plaintext)
            f.flush()
            os.fsync(f.fileno())

        os.replace(temp, PLAINTEXT_DB)

    finally:
        if temp.exists():
            temp.unlink()


def validate_database():
    conn = sqlite3.connect(
        f"file:{PLAINTEXT_DB}?mode=rw",
        uri=True,
    )

    try:
        result = conn.execute(
            "PRAGMA integrity_check"
        ).fetchone()

        if not result or result[0] != "ok":
            raise ValueError("SQLite integrity check failed.")

    finally:
        conn.close()


def encrypt_file(password: str):
    data = PLAINTEXT_DB.read_bytes()

    salt = secrets.token_bytes(SALT_SIZE)
    nonce = secrets.token_bytes(NONCE_SIZE)
    key = derive_key(password, salt)

    ciphertext = AESGCM(key).encrypt(
        nonce,
        data,
        MAGIC,
    )

    temp = ENCRYPTED_DB.with_name(
        ENCRYPTED_DB.name + ".tmp"
    )

    try:
        with temp.open("wb") as f:
            f.write(MAGIC)
            f.write(salt)
            f.write(nonce)
            f.write(ciphertext)
            f.flush()
            os.fsync(f.fileno())

        os.replace(temp, ENCRYPTED_DB)

    finally:
        if temp.exists():
            temp.unlink()


def cleanup_extracted_files():
    for name in EXTRACTED_FILES:
        path = BASE_DIR / name
        try:
            path.unlink()
        except FileNotFoundError:
            pass


class PasswordScreen(App):
    CSS = """
    Screen {
        align: center middle;
    }

    #box {
        width: 72;
        height: auto;
        border: round cyan;
        padding: 2 4;
    }

    #title {
        text-style: bold;
        text-align: center;
        margin-bottom: 1;
    }

    #password {
        margin: 1 0;
    }

    #buttons {
        width: 100%;
        height: 5;
        align: center middle;
    }

    #buttons Button {
        width: 20;
        height: 3;
        margin: 0 1;
        content-align: center middle;
    }

    #status {
        height: 2;
        color: yellow;
        text-align: center;
    }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.password_changed = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Container(id="box"):
            yield Label(
                "🔐  Encrypted SQLite Database",
                id="title",
            )

            yield Label(
                "Enter the database password:"
            )

            yield Input(
                placeholder="Password",
                password=True,
                id="password",
            )

            yield Label("", id="status")

            with Horizontal(id="buttons"):
                yield Button(
                    "Decrypt",
                    variant="success",
                    id="decrypt",
                )

                yield Button(
                    "Change Password",
                    variant="primary",
                    id="change_password",
                )

                yield Button(
                    "Cancel",
                    variant="error",
                    id="cancel",
                )

        yield Footer()

    def on_mount(self):
        self.query_one("#password").focus()

    def try_decrypt(self):
        password_input = self.query_one("#password")
        password = password_input.value

        if not password:
            self.query_one("#status").update(
                "Password cannot be empty."
            )
            return

        try:
            decrypt_file(password)
            validate_database()

        except Exception:
            if PLAINTEXT_DB.exists():
                PLAINTEXT_DB.unlink()

            self.query_one("#status").update(
                "❌ Incorrect password or invalid database."
            )

            password_input.value = ""
            password_input.focus()
            return

        self.password_changed = False
        self.exit((password, self.password_changed))

    def change_password(self):
        password_input = self.query_one("#password")
        current_password = password_input.value

        if not current_password:
            self.query_one("#status").update(
                "Enter the current password first."
            )
            password_input.focus()
            return

        try:
            decrypt_file(current_password)
            validate_database()

        except Exception:
            if PLAINTEXT_DB.exists():
                PLAINTEXT_DB.unlink()

            self.query_one("#status").update(
                "❌ Incorrect current password."
            )

            password_input.value = ""
            password_input.focus()
            return

        password_input.value = ""
        password_input.placeholder = "Enter NEW password"
        password_input.password = True

        self.query_one("#status").update(
            "Enter the new password and press Enter."
        )

        self._current_password = current_password
        self._changing_password = True

        password_input.focus()

    def submit_new_password(self):
        new_password = self.query_one("#password").value

        if not new_password:
            self.query_one("#status").update(
                "New password cannot be empty."
            )
            return

        if new_password == self._current_password:
            self.query_one("#status").update(
                "New password must be different."
            )
            return

        self.password_changed = True
        self.exit((new_password, self.password_changed))

    def on_input_submitted(
        self,
        event: Input.Submitted,
    ):
        if event.input.id != "password":
            return

        if getattr(self, "_changing_password", False):
            self.submit_new_password()
        else:
            self.try_decrypt()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "cancel":
            self.exit(False)
            return

        if event.button.id == "decrypt":
            self.try_decrypt()
            return

        if event.button.id == "change_password":
            self.change_password()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--extractor-version", default="0", help="Current extractor version")
    args, _ = parser.parse_known_args()

    local_version = args.extractor_version

    print(f"Checking for updates (Local Version: {local_version})...")
    remote_version = check_remote_version()

    try:
        remote_int = int(remote_version)
        local_int = int(local_version)
    except ValueError:
        remote_int = 0
        local_int = 0

    if remote_int > local_int:
        print(f"Newer extractor version found on Google Drive (v{remote_int} > v{local_int}). Downloading update...")
        extractor_path = BASE_DIR / "self_extractor.py"
        if download_and_update_extractor(extractor_path):
            print("Update downloaded successfully. Restarting extractor...")
            cleanup_extracted_files()
            os.execv(sys.executable, [sys.executable, str(extractor_path)])
        else:
            print("Failed to update extractor. Continuing with local version...", file=sys.stderr)

    if not ENCRYPTED_DB.is_file():
        print("ERROR: data.db.enc not found.")
        return 1

    if not APP.is_file():
        print("ERROR: app.py not found.")
        return 1

    if PLAINTEXT_DB.exists():
        print(
            "ERROR: data.db already exists. "
            "Refusing to overwrite it."
        )
        return 1

    screen_result = PasswordScreen().run()

    if not screen_result:
        cleanup_extracted_files()
        return 0

    password, password_changed = screen_result

    initial_db_sha = get_file_sha256(PLAINTEXT_DB)

    try:
        print("Starting app.py...")

        process = subprocess.Popen(
            [sys.executable, str(APP)],
            cwd=BASE_DIR,
        )

        try:
            exit_code = process.wait()

        except KeyboardInterrupt:
            process.terminate()

            try:
                exit_code = process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                exit_code = process.wait()

    finally:
        if PLAINTEXT_DB.exists():
            new_db_sha = get_file_sha256(PLAINTEXT_DB)

            print("Re-encrypting data.db...")

            try:
                encrypt_file(password)

            except Exception as exc:
                print(
                    "CRITICAL ERROR: Could not re-encrypt "
                    f"data.db: {exc}",
                    file=sys.stderr,
                )
                print(
                    "Plaintext data.db has NOT been deleted.",
                    file=sys.stderr,
                )
                return 2

            PLAINTEXT_DB.unlink()

            print("Database encrypted.")
            print("Plaintext database removed.")
            print("Rebuilding the self-extractor...")

            current_ver = check_remote_version()
            try:
                next_ver = str(int(current_ver) + 1)
            except ValueError:
                next_ver = "1"

            selected_files = list(EXTRACTED_FILES[1:])

            create_self_extractor(
                ".",
                selected_files,
                version=next_ver,
                output_py_path="self_extractor.py",
            )

            if new_db_sha != initial_db_sha or password_changed:
                print("Changes detected in data.db or password updated. Uploading updated self_extractor.py...")
                upload_self_extractor(BASE_DIR / "self_extractor.py", next_ver)
            else:
                print("No changes detected in data.db or password. Keeping existing self_extractor.py on server.")

            cleanup_extracted_files()

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())