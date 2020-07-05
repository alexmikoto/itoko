from abc import ABC, abstractmethod
from typing import Optional

import magic

from itoko.fs.generators import default_filename_generator


class FormatReader(ABC):
    @abstractmethod
    def complies(self, payload: bytes) -> bool:
        raise NotImplementedError

    @abstractmethod
    def read(self, filename: str, payload: bytes) -> "FormatFile":
        raise NotImplementedError


class FormatFile(ABC):
    __slots__ = (
        "_payload",
        "_fs_filename",
        "_is_encrypted",
        "_filename",
        "_mime_type",
    )

    _payload: bytes
    _fs_filename: str
    _is_encrypted: bool
    _filename: Optional[str]
    _mime_type: Optional[str]

    def __init__(
        self,
        payload: bytes,
        fs_filename: str = None,
        is_encrypted: bool = False,
        filename: str = None,
        mime_type: str = None,
    ):
        self._payload = payload
        self._fs_filename = fs_filename or default_filename_generator()
        self._is_encrypted = is_encrypted
        self._filename = filename
        if self._is_encrypted:
            self._mime_type = mime_type
        else:
            # Try to guess MIME type if we are not encrypted and ONLY IF
            self._mime_type = mime_type or magic.from_buffer(payload, mime=True)

    @classmethod
    @abstractmethod
    def read(cls, filename: str, payload: bytes) -> "FormatFile":
        """
        Reads a FormatFile object from a binary file.

        :return: FormatFile object.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def file(self) -> bytes:
        """
        Returns the binary representation of the current object.

        :return: Raw binary file with format headers.
        """
        raise NotImplementedError

    @property
    def payload(self) -> bytes:
        """
        Returns the binary payload wrapped by the current file object.

        :return: Binary payload wrapped by the current object.
        """
        if self._is_encrypted:
            raise TypeError("Cannot read the payload in an encrypted file.")
        return self._payload

    @property
    def fs_filename(self) -> str:
        """
        Returns the filename of the current file as is stored in the server.

        :return: Filename of the current file.
        """
        return self._fs_filename

    @property
    def is_encrypted(self) -> bool:
        """
        Returns whether the current object represents an encrypted file or an
        unencrypted file. Take note reading the payload from an encrypted file
        will result in garbage.

        :return: Boolean flag indicating if file is encrypted.
        """
        return self._is_encrypted

    @property
    def filename(self):
        """
        Returns the original filename of the current file as was sent to the
        server.

        :return: Original filename of the current file.
        """
        if self._is_encrypted:
            raise TypeError("Cannot read the filename in an encrypted file.")
        return self._filename

    @property
    def mime_type(self):
        """
        Returns the MIME type of the current file.

        :return: MIME type of the current file.
        """
        if self._is_encrypted:
            raise TypeError("Cannot read the MIME type in an encrypted file.")
        return self._mime_type

    def encrypt(self, key: bytes) -> "FormatFile":
        """
        Encrypts the payload in the current file object and return a copy with
        the encrypted data.
        """
        if self.is_encrypted:
            raise TypeError("File already encrypted.")
        return self.encryptor(key)

    @abstractmethod
    def encryptor(self, key: bytes) -> "FormatFile":
        """
        Function to be called when attempting to encrypt the payload. Operations
        are expected to perform a copy.
        """
        raise NotImplementedError

    def decrypt(self, key: bytes) -> "FormatFile":
        """
        Decrypts the payload in the current file object and return a copy with
        the decrypted data.
        """
        if not self.is_encrypted:
            raise TypeError("File not encrypted.")
        return self.decryptor(key)

    @abstractmethod
    def decryptor(self, key: bytes) -> "FormatFile":
        """
        Function to be called when attempting to decrypt the payload. Operations
        are expected to perform a copy.
        """
        raise NotImplementedError
