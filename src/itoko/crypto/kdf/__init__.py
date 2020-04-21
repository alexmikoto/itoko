from abc import ABC, abstractmethod

from .exc import InvalidKeyLengthError

__all__ = ["KDF", "DerivedKey"]


class DerivedKey(ABC):
    """
    Stores the results from the key derivation function. Only authenticated
    ciphers
    """
    __slots__ = ("_key_length", "key", "salt", "derived_key")

    _key_length: int

    key: bytes
    salt: bytes
    derived_key: bytes

    def __init__(
        self, key_length: int, key: bytes, salt: bytes, derived_key: bytes
    ) -> None:
        self._key_length = key_length
        self.key = key
        self.salt = salt
        self.derived_key = derived_key

    @property
    def cipher_key(self):
        """
        The first bits of the derived key are used as cipher encryption key.
        """
        return self.derived_key[:self._key_length]

    @property
    def hmac_key(self):
        """
        The last bits of the derived key are used as MAC key.
        """
        return self.derived_key[-self._key_length:]


class KDF(ABC):
    """
    Basic interface for key derivation suites.
    """
    __slots__ = ("key_length", "iterations")

    default_key_length = None
    supported_key_lengths = ()

    key_length: int
    iterations: int

    def __init__(self, key_length: int, iterations: int) -> None:
        """
        Instance the given KDF suite.

        :param key_length:
        :param iterations:
        """
        self.key_length = self._valid_key_length(key_length)
        self.iterations = iterations

    def _valid_key_length(self, key_length: int = None) -> int:
        if not key_length:
            return self.default_key_length
        else:
            if key_length not in self.supported_key_lengths:
                raise InvalidKeyLengthError
            return key_length

    @abstractmethod
    def derive_key(self, key: bytes, salt: bytes) -> DerivedKey:
        """
        Derives a cryptographic fixed-length key from the given key.

        :param key: Plaintext key.
        :param salt: Salt value.
        """
        raise NotImplementedError
