from cryptography.hazmat.backends  import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher as CryptoCipher

from itoko.crypto.kdf import DerivedKey

__all__ = ["Cipher"]


class Cipher:
    __slots__ = ('key', 'nonce', 'cipher')

    key: DerivedKey
    iv: bytes
    nonce: bytes

    _algorithm: CryptoCipher = None
    _backend: object  # Cryptography backends are not strongly typed

    def __init__(self, key: DerivedKey, nonce: bytes):
        self.key = key
        self.nonce = nonce
        self.cipher = self._build_cipher(key, nonce)

    def _build_cipher(self, key: DerivedKey, nonce: bytes) -> CryptoCipher:
        raise NotImplementedError

    def encrypt(self, plaintext: bytes) -> bytes:
        """
        Encrypts plaintext with AES in CTR mode.
        """
        encryptor = self.cipher.encryptor()
        return encryptor.update(plaintext) + encryptor.finalize()

    def decrypt(self, encrypted: bytes) -> bytes:
        """
        Decrypts ciphertext with AES in CTR mode.
        """
        decryptor = self.cipher.decryptor()
        return decryptor.update(encrypted) + decryptor.finalize()
