from abc import ABC, abstractmethod

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.hmac import HMAC as CryptoHMAC

from itoko.crypto.exc import DecryptionError
from itoko.crypto.kdf import DerivedKey

__all__ = ["HMAC"]


class HMAC(ABC):
    __slots__ = ("key", "_hmac")

    digest_size: int = None

    key: DerivedKey

    _hmac: CryptoHMAC

    def __init__(self, key: DerivedKey):
        self.key = key
        self._hmac = self._build_hmac()

    @abstractmethod
    def _build_hmac(self) -> CryptoHMAC:
        raise NotImplementedError

    def build(self, ciphertext: bytes):
        """
        Builds an HMAC over a given ciphertext with the current HMAC key.

        :return: Computed HMAC.
        """
        self._hmac.update(ciphertext)
        return self._hmac.finalize()

    def check(self, ciphertext: bytes, hmac: bytes):
        """
        Checks whether a given ciphertext matches a given HMAC with the current
        HMAC key.

        :param ciphertext: Raw ciphertext bytes.
        :param hmac: Previously obtained HMAC.
        :return:
        """
        try:
            self._hmac.update(ciphertext)
            self._hmac.verify(hmac)
        except InvalidSignature as e:
            raise DecryptionError from e
