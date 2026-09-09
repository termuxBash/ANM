import sqlite3
import subprocess
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
import getpass

SALT_LEN = 16

class Data:
    def __init__(self, path: str, password: str):
            self.path = path
            self.password = password
            self.conn = None
    
    def derive_key(password: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480_000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))


    def extract(enc_path: str, out_path: str, password: str):
        """Decrypt enc_path and write plaintext sqlite db to out_path in current dir."""
        with open(enc_path, "rb") as f:
            blob = f.read()
        salt, encrypted = blob[:SALT_LEN], blob[SALT_LEN:]
        key = self.derive_key(password, salt)
        try:
            plain = Fernet(key).decrypt(encrypted)
        except Exception:
            raise ValueError("Wrong password or corrupted database")

        with open(out_path, "wb") as f:
            f.write(plain)
        print(f"Extracted plaintext db to {out_path}")


    def repack(enc_path: str, plain_path: str, password: str):
        """Re-encrypt plain_path back into enc_path, keeping the original salt."""
        with open(enc_path, "rb") as f:
            old_blob = f.read()
        salt = old_blob[:SALT_LEN]

        with open(plain_path, "rb") as f:
            plain = f.read()

        key = derive_key(password, salt)
        encrypted = Fernet(key).encrypt(plain)

        with open(enc_path, "wb") as f:
            f.write(salt + encrypted)
        print(f"Repacked {plain_path} -> {enc_path}")


    def create_new(enc_path: str, password: str):
        """Create a brand-new encrypted db with an empty sqlite file inside."""
        salt = os.urandom(SALT_LEN)
        tmp_plain = enc_path + ".plain.tmp"
        sqlite3.connect(tmp_plain).close()  # creates a valid empty sqlite file

        with open(tmp_plain, "rb") as f:
            plain = f.read()
        os.remove(tmp_plain)

        key = derive_key(password, salt)
        encrypted = Fernet(key).encrypt(plain)
        with open(enc_path, "wb") as f:
            f.write(salt + encrypted)
        print(f"Created new encrypted db: {enc_path}")


if __name__ == "__main__":
    enc_path = "mydata.db"
    plain_path = "mydata_extracted.db"  # plaintext copy, current dir, for testing

    password = getpass.getpass("Password: ")

    if not os.path.exists(enc_path):
        create_new(enc_path, password)

    extract(enc_path, plain_path, password)

    print(f"Open it with: sqlite3 {plain_path}")
    print("When done, run repack() to re-encrypt your changes back.")