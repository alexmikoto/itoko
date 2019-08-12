from abc import ABC, abstractmethod

__all__ = ["KDFSuite", "DerivedKey", "InvalidKeyLengthError"]


class InvalidKeyLengthError(Exception):
    """
    Raised when the specified key length is not supported by the current key
    derivation suite.
    """


class KDFSuite(ABC):
    """
    Basic interface for key derivation suites.
    """

    default_key_length = None
    supported_key_lengths = ()

    def __init__(self, key_length: int) -> None:
        self.key_length = self._valid_key_lenth(key_length)

    def  _valid_key_lenth(self, key_length: int=None) -> int:
        if not key_length:
            return self.default_key_length
        else:
            if key_length not in self.supported_key_lengths:
                raise InvalidKeyLengthError
            return key_length


class DerivedKey(ABC):
    """
    Basic interface for key derivation suites.
    """
    __slots__ = ("key", "salt", "key_length", "derived_key")

    def __init__(self, key: bytes, salt: bytes, key_length: int=None) -> None:
        self.key = key
        self.salt = salt
        self.derived_key = self.derive_key(key, salt)


    @abstractmethod
    def derive_key(self, key: bytes, salt: bytes) -> bytes:
        """
        Derives a cryptographic fixed-length key from the given key.

        :param key: Plaintext key.
        :param salt: Salt value.
        """
        raise NotImplementedError
