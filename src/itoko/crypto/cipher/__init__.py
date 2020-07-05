from abc import ABC, abstractmethod
from typing import Optional

from cryptography.hazmat.primitives.ciphers import Cipher as CryptoCipher

from itoko.crypto.kdf import DerivedKey

__all__ = ["Cipher"]


class Cipher(ABC):
    __slots__ = ("key", "iv", "nonce", "_cipher")

    key: DerivedKey
    iv: Optional[bytes]
    nonce: Optional[bytes]

    _cipher: CryptoCipher

    def __init__(self, key: DerivedKey, iv: bytes = None, nonce: bytes = None):
        self.key = key
        self.iv = iv
        self.nonce = nonce
        self._cipher = self._build_cipher()

    @abstractmethod
    def _build_cipher(self) -> CryptoCipher:
        raise NotImplementedError

    def encrypt(self, plaintext: bytes) -> bytes:
        """
        Encrypts plaintext with chosen algorithm.
        """
        encryptor = self._cipher.encryptor()
        return encryptor.update(plaintext) + encryptor.finalize()

    def decrypt(self, encrypted: bytes) -> bytes:
        """
        Decrypts ciphertext with chosen algorithm.
        """
        decryptor = self._cipher.decryptor()
        return decryptor.update(encrypted) + decryptor.finalize()
