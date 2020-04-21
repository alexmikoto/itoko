import os

from cryptography.hazmat.backends import default_backend

from itoko.crypto.kdf.pbkdf import PBKDFSuite
from itoko.crypto.cipher.aes import AESCipher

KEY_LENGTH = 32
SALT_SIZE = 16
BLOCK_SIZE = 16
ITERATION_COUNT = 100000

backend = default_backend()


class AESv1Suite:
    """
    Handles encryption and decryption with AES-128-HMAC in CTR mode.
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
        salt = os.urandom(SALT_SIZE)
        nonce = os.urandom(BLOCK_SIZE)
        key = PBKDFSuite(ITERATION_COUNT, ).derive_key(self.key, salt)
        cipher = AESCipher(key, nonce)
        encrypted = cipher.encrypt(plaintext)
        # Concat the CTR nonce before building the HMAC to verify it too
        encrypted = nonce + encrypted
        hmac = key.build_hmac(encrypted)
        return b''.join([encrypted, hmac, salt])

    def decrypt(self, encrypted: bytes) -> bytes:
        """
        Decrypts a bundle using the provided key. The PBKDF2 salt is taken from
        the bundle. If the provided key and salt fail to verify the HMAC
        AESCipherException is raised.
        """
        encrypted, hmac, salt = (
            encrypted[:-(SALT_SIZE + hashes.SHA256.digest_size)],
            encrypted[-(SALT_SIZE + hashes.SHA256.digest_size): -SALT_SIZE],
            encrypted[-SALT_SIZE:]
        )
        key = DerivedKey(self.key, salt)
        # Check the HMAC before going further
        key.check_hmac(encrypted, hmac)
        nonce, encrypted = encrypted[:BLOCK_SIZE], encrypted[BLOCK_SIZE:]
        cipher = AESCipher(key, nonce)
        return cipher.decrypt(encrypted)
