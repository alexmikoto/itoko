from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import (
    Cipher as CryptoCipher,
    algorithms,
    modes,
)

from itoko.crypto.cipher import Cipher

__all__ = ["AESCTRCipher"]


class AESCTRCipher(Cipher):
    def _build_cipher(self) -> CryptoCipher:
        return CryptoCipher(
            algorithms.AES(self.key.cipher_key),
            modes.CTR(self.nonce),
            backend=default_backend(),
        )
