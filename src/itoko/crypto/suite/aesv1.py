import os

from cryptography.hazmat.backends import default_backend

from itoko.crypto.kdf.pbkdf import PBKDF
from itoko.crypto.cipher.aesctr import AESCTRCipher
from itoko.crypto.hmac.sha256 import SHA256HMAC
from itoko.crypto.suite import Suite

backend = default_backend()


class AESv1Suite(Suite):
    """
    Handles encryption and decryption with AES-256-HMAC in CTR mode.
    """

    __slots__ = ("key",)

    SUITE_ID = 1

    KEY_LENGTH = 32
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
        return b"".join([encrypted, hh, salt])

    def decrypt(self, ciphertext: bytes) -> bytes:
        """
        Decrypts a bundle using the provided key. The PBKDF2 salt is taken from
        the bundle. If the provided key and salt fail to verify the HMAC
        AESCipherException is raised.
        """
        payload, hh, salt = (
            ciphertext[: -(self.SALT_SIZE + SHA256HMAC.digest_size)],
            ciphertext[
                -(self.SALT_SIZE + SHA256HMAC.digest_size): -self.SALT_SIZE
            ],
            ciphertext[-self.SALT_SIZE:],
        )
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
