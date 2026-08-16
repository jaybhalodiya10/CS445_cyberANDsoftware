import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

class AES128Cipher:
    
    def __init__(self, key=None, iv=None):
        self.key = key if key else os.urandom(16)
        self.iv = iv if iv else os.urandom(16)

    def encrypt(self, data: bytes) -> bytes:
        
        padded_data = pad(data, AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        return cipher.encrypt(padded_data)

    def encrypt_prepadded(self, padded_data: bytes) -> bytes:

        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        return cipher.encrypt(padded_data)
