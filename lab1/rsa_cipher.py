from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

class RSACipher:

    def __init__(self):
        self.key = RSA.generate(2048)

        self.cipher = PKCS1_OAEP.new(self.key)
        self.block_size = 214

    def encrypt(self, data):
        encrypted_data = b""

        for i in range(0, len(data), self.block_size):
            block = data[i:i + self.block_size]
            encrypted_data += self.cipher.encrypt(block)

        return encrypted_data