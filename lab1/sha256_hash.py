from Crypto.Hash import SHA256

class SHA256Hash:
    def encrypt(self, data: bytes) -> bytes:
        # Although hashing isn't encryption, we follow the same interface format
        hasher = SHA256.new(data)
        return hasher.digest()
