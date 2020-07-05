from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from itoko.crypto.kdf import KDF, DerivedKey

__all__ = ["PBKDF", "PBKDFDerivedKey"]

backend = default_backend()


class PBKDFDerivedKey(DerivedKey):
    """
    PBKDF2-HMAC derived key.
    """

    pass


class PBKDF(KDF):
    """
    Suite that uses PBKDF2-HMAC as KDF, using SHA256 as PRF.
    """

    default_key_length = 64
    supported_key_lengths = (16, 32, 64)

    def derive_key(self, key: bytes, salt: bytes) -> DerivedKey:
        """
        Derives a cryptographic fixed-length key from the given key.

        :param key: Plaintext key.
        :param salt: PBKDF2 salt value.
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256,
            length=self.key_length,
            salt=salt,
            iterations=self.iterations,
            backend=backend,
        )
        return PBKDFDerivedKey(
            key_length=self.key_length,
            key=key,
            salt=salt,
            derived_key=kdf.derive(key),
        )
