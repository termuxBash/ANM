#!/usr/bin/env python3

import hashlib
import os
import secrets
import getpass
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


BASE_DIR = Path(__file__).resolve().parent
PLAINTEXT_DB = BASE_DIR / "data.db"
ENCRYPTED_DB = BASE_DIR / "data.db.enc"

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



def main():
    if not PLAINTEXT_DB.is_file():
        print("ERROR: data.db was not found.")
        return 1

    if ENCRYPTED_DB.exists():
        print("ERROR: data.db.enc already exists.")
        print("Delete it first if you really want to replace it.")
        return 1

    password = getpass.getpass("Enter encryption password: ")

    if not password:
        print("ERROR: Password cannot be empty.")
        return 1

    confirm = getpass.getpass("Confirm password: ")

    if password != confirm:
        print("ERROR: Passwords do not match.")
        return 1

    print("Encrypting data.db...")

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

    print("Successfully created:")
    print(f"  {ENCRYPTED_DB}")
    print()
    print("Original data.db was NOT deleted.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())