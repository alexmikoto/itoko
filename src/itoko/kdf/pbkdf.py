from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from itoko.kdf import DerivedKey

__all__ = ["PBKDFDerivedKey"]

ITERATION_COUNT = 100000

backend = default_backend()


class PBKDFDerivedKey(DerivedKey):
    """
    Suite that uses PBKDF2-HMAC as KDF, using SHA256 as PRF.
    """

    default_key_length = 64
    supported_key_lengths = (32, 64)

    def derive_key(self, key: bytes, salt: bytes) -> bytes:
        """
        Derives a cryptographic fixed-length key from the given key.

        :param key: Plaintext key.
        :param salt: PBKDF2 salt value.
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256,
            length=self.key_length,
            salt=salt,
            iterations=ITERATION_COUNT,
            backend=backend
        )
        return kdf.derive(key)
