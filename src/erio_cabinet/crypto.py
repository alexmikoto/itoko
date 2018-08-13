"""
Handles the encryption of files and the binary protocol for storage of encrypted
files.
"""

import base64
import os
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.hmac import HMAC
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

KEY_LENGTH = 32
SALT_SIZE = 16
BLOCK_SIZE = 16
ITERATION_COUNT = 100000

backend = default_backend()


def generate_key() -> bytes:
    """
    Generates a random key by passing /dev/urandom through URL-safe base64
    encoding.
    """
    return base64.urlsafe_b64encode(os.urandom(18))


class DecryptionError(Exception):
    """
    Raised when an HMAC verification fails.
    """
    pass


class DerivedKey:
    def __init__(self, key: bytes, salt: bytes) -> None:
        self.key = key
        self.salt = salt
        self.derived_key = self._derive_key(key, salt)

    @staticmethod
    def _derive_key(key: bytes, salt: bytes) -> bytes:
        """
        Derives a cryptographic key from the given key. The key derivation
        function used is PBKDF2 with SHA256-HMAC as a PRF.

        :param key: Plaintext key.
        :param salt: PBKDF2 salt.
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256,
            length=2 * KEY_LENGTH,
            salt=salt,
            iterations=ITERATION_COUNT,
            backend=backend
        )
        return kdf.derive(key)

    @property
    def cipher_key(self) -> bytes:
        """
        The first 128 bits of the derived key are used as cipher encryption key.
        """
        return self.derived_key[:KEY_LENGTH]

    @property
    def hmac_key(self) -> bytes:
        """
        The last 128 bits of the derived key are used as MAC key.
        """
        return self.derived_key[-KEY_LENGTH:]

    def build_hmac(self, ciphertext: bytes):
        """
        Builds an HMAC over a given ciphertext with the current HMAC key.

        :return: Computed HMAC.
        """
        h = HMAC(self.hmac_key, hashes.SHA256(), backend=backend)
        h.update(ciphertext)
        return h.finalize()

    def check_hmac(self, ciphertext: bytes, hmac: bytes):
        """
        Checks whether a given ciphertext matches a given HMAC with the current
        HMAC key.

        :param ciphertext: Raw ciphertext bytes.
        :param hmac: Previously obtained HMAC.
        :return:
        """
        try:
            h = HMAC(self.hmac_key, hashes.SHA256(), backend=backend)
            h.update(ciphertext)
            h.verify(hmac)
        except InvalidSignature as e:
            raise DecryptionError(e)


class AESCipher:
    __slots__ = ('key', 'nonce', 'cipher')

    def __init__(self, key: DerivedKey, nonce: bytes):
        self.key = key
        self.nonce = nonce
        self.cipher = self._build_cipher(key, nonce)

    @staticmethod
    def _build_cipher(key: DerivedKey, nonce: bytes):
        return Cipher(
            algorithms.AES(key.cipher_key),
            modes.CTR(nonce),
            backend=backend
        )

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


class Encryptor:
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
        key = DerivedKey(self.key, salt)
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
