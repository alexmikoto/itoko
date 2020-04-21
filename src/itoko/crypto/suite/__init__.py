
class Encryptor:
    """
    Handles encryption and decryption with preset parameters.
    """
    __slots__ = ('key',)

    def __init__(self, key: bytes):
        self.key = key

    def encrypt(self, plaintext: bytes) -> bytes:
        """
        Encrypts-then-HMACs plaintext with AES in CTR mode. The key is derived
        through PBKDF2 over the provided key. Returns a bundle including
        ciphertext, nonce, HMAC and PBKDF2 salt.
        """
        raise NotImplementedError

    def decrypt(self, encrypted: bytes) -> bytes:
        """
        Decrypts a bundle using the provided key. The PBKDF2 salt is taken from
        the bundle. If the provided key and salt fail to verify the HMAC
        AESCipherException is raised.
        """
        raise NotImplementedError


class Suite:
    """
    Handles encryption and decryption with preset parameters.
    """
    __slots__ = ('key',)

    def __init__(self, key: bytes):
        self.key = key

    def encryptor(self, key: bytes) -> Encryptor:
        """
        Encrypts-then-HMACs plaintext with AES in CTR mode. The key is derived
        through PBKDF2 over the provided key. Returns a bundle including
        ciphertext, nonce, HMAC and PBKDF2 salt.
        """
        raise NotImplementedError


