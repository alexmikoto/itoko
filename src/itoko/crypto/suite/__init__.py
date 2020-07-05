from abc import ABC, abstractmethod

__all__ = ["Suite"]


class Suite(ABC):
    """
    Handles encryption and decryption with preset parameters. The used
    algorithms and encryption header formats may vary per suite.
    """

    __slots__ = ("key",)

    def __init__(self, key: bytes):
        self.key = key

    @abstractmethod
    def encrypt(self, plaintext: bytes) -> bytes:
        """
        Encrypt the given plaintext using the suite parameters.
        """
        raise NotImplementedError

    @abstractmethod
    def decrypt(self, ciphertext: bytes) -> bytes:
        """
        Decrypts a bundle using the suite parameters.
        """
        raise NotImplementedError
