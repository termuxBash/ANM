#!/usr/bin/env python3

import hashlib
import os
import secrets
import sqlite3
import subprocess
import sys
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

        # Return both the old password and the password
        # that should be used for re-encryption.
        self.exit(password)

    def change_password(self):
        """
        First verify the current password, then ask for
        the new password.
        """
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

        # Current password is valid.
        #
        # Change the input into a new-password field.
        password_input.value = ""
        password_input.placeholder = "Enter NEW password"
        password_input.password = True

        self.query_one("#status").update(
            "Enter the new password and press Enter."
        )

        # Store the current password so the submit handler
        # knows we are in password-change mode.
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

        # Database is already decrypted and validated.
        # Return the NEW password so main() uses it when
        # re-encrypting the database.
        self.exit(new_password)

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

    # Textual password UI.
    #
    # This now returns the password that should be used
    # for the FINAL encryption. If the user selected
    # "Change Password", this is the NEW password.
    password = PasswordScreen().run()

    if not password:
        cleanup_extracted_files()
        return 0

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
        # Always encrypt using the password returned by
        # PasswordScreen.
        if PLAINTEXT_DB.exists():
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

            selected_files = list(EXTRACTED_FILES[1:])

            create_self_extractor(
                ".",
                selected_files,
                output_py_path="self_extractor.py",
            )

            cleanup_extracted_files()

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())