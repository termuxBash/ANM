import sqlite3
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

SALT_LEN = 16

def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480_000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


class EncryptedDB:
    def __init__(self, path: str, password: str):
        self.path = path
        self.password = password
        self.conn = None

    def decrypt(self):
        
    def open(self):
        is_new = not os.path.exists(self.path)

        if is_new:
            self.conn = sqlite3.connect(":memory:")
            return self.conn  # salt gets generated + written on first save()

        with open(self.path, "rb") as f:
            blob = f.read()
        salt, encrypted = blob[:SALT_LEN], blob[SALT_LEN:]
        key = derive_key(self.password, salt)
        fernet = Fernet(key)

        try:
            decrypted = fernet.decrypt(encrypted)
        except Exception:
            raise ValueError("Wrong password or corrupted database")

        self.conn = sqlite3.connect(":memory:")
        self.conn.deserialize(decrypted)
        return self.conn

    def save(self):
        self.conn.commit()

        if os.path.exists(self.path):
            with open(self.path, "rb") as f:
                salt = f.read(SALT_LEN)
        else:
            salt = os.urandom(SALT_LEN)

        key = derive_key(self.password, salt)
        fernet = Fernet(key)
        plain = self.conn.serialize()
        encrypted = fernet.encrypt(plain)

        with open(self.path, "wb") as f:
            f.write(salt + encrypted)

    def close(self):
        self.save()
        self.conn.close()