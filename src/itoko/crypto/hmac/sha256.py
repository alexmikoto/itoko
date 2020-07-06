from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.hmac import HMAC as CryptoHMAC, hashes

from itoko.crypto.hmac import HMAC

__all__ = ["SHA256HMAC"]


class SHA256HMAC(HMAC):
    digest_size = hashes.SHA256.digest_size

    def _build_hmac(self) -> CryptoHMAC:
        return CryptoHMAC(
            self.key.hmac_key, hashes.SHA256(), backend=default_backend()
        )
