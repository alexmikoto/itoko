import os
import struct

from cryptography.hazmat.backends import default_backend

from itoko.crypto.kdf.pbkdf import PBKDF
from itoko.crypto.cipher.aesctr import AESCTRCipher
from itoko.crypto.hmac.sha256 import SHA256HMAC
from itoko.crypto.suite import Suite

backend = default_backend()


class AESv2Suite(Suite):
    """
    Handles encryption and decryption with AES-256-HMAC in CTR mode. This new
    version additionally uses a new header layout.
    """

    __slots__ = ("key",)

    SUITE_ID = 2
    HEADER_FORMAT = "!H6x16s16x32s"
    HEADER_SIZE = struct.calcsize("!H6x16s16x32s")

    # 256-bit key
    KEY_LENGTH = 32
    # AES blocks are always 128 bits
    SALT_SIZE = 16
    BLOCK_SIZE = 16
    ITERATION_COUNT = 100000

    def _get_kdf(self):
        return PBKDF(self.KEY_LENGTH * 2, self.ITERATION_COUNT)

    def encrypt(self, plaintext: bytes) -> bytes:
        """
        Encrypts-then-HMACs plaintext with AES in CTR mode. The key is derived
        through PBKDF2 over the provided key. Returns a bundle including
        ciphertext, nonce, HMAC and PBKDF2 salt.
        """
        salt = os.urandom(self.SALT_SIZE)
        nonce = os.urandom(self.BLOCK_SIZE)
        # In this suite we split the derived key in two segments
        kdf = self._get_kdf()
        dk = kdf.derive_key(self.key, salt)
        cipher = AESCTRCipher(dk, nonce=nonce)
        encrypted = cipher.encrypt(plaintext)
        # Make the CTR nonce the first block and use the HMAC to verify it too
        encrypted = nonce + encrypted
        hmac = SHA256HMAC(dk)
        hh = hmac.build(encrypted)
        # Build crypto header
        header = struct.pack(self.HEADER_FORMAT, self.SUITE_ID, salt, hh)
        return header + encrypted

    def decrypt(self, ciphertext: bytes) -> bytes:
        """
        Decrypts a bundle using the provided key. The PBKDF2 salt is taken from
        the bundle. If the provided key and salt fail to verify the HMAC
        AESCipherException is raised.
        """
        header, payload = (
            ciphertext[: self.HEADER_SIZE],
            ciphertext[self.HEADER_SIZE:],
        )
        _, salt, hh = struct.unpack(self.HEADER_FORMAT, header)
        kdf = self._get_kdf()
        dk = kdf.derive_key(self.key, salt)
        # Check the HMAC before going further
        hmac = SHA256HMAC(dk)
        hmac.check(payload, hh)
        # CTR nonce is the first block
        nonce, encrypted = (
            payload[: self.BLOCK_SIZE],
            payload[self.BLOCK_SIZE:],
        )
        cipher = AESCTRCipher(dk, nonce=nonce)
        return cipher.decrypt(encrypted)
