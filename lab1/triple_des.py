import os
from Crypto.Cipher import DES3
from Crypto.Util.Padding import pad

class TripleDESCipher:
    def __init__(self, key=None, iv=None):
        # 24 bytes (192 bits) key is required for Triple DES
        self.key = key if key else DES3.adjust_key_parity(os.urandom(24))
        self.iv = iv if iv else os.urandom(8)

    def encrypt(self, data: bytes) -> bytes:
        padded_data = pad(data, DES3.block_size)
        cipher = DES3.new(self.key, DES3.MODE_CBC, self.iv)
        return cipher.encrypt(padded_data)
