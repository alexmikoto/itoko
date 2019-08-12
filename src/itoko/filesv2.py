"""
Handles the binary protocol for files, embedded file metadata and server-side
file storage.

The binary protocol includes a single byte header that indicates if the file is
encrypted or not.

The raw file is stored with an additional variable length footer with the
original filename. The last 6 bytes store the base 10 representation of the
filename length, and the previous N bytes store the filename as a string.

Header layout:
| Encrypted? (1 byte, '1' or '0') | Raw data |

Footer layout:
| Raw data | Filename (N bytes) | Filename length (6 bytes) |

NEW Header layout:
typedef struct header {
    uint8_t version;
    uint8_t flags;
    uint16_t filename_length;
};

"""

import os
import time
import struct

from werkzeug.datastructures import FileStorage

from itoko.crypto import Encryptor

__all__ = [
    "generate_filename",
    "file_from_file_storage",
    "read_file",
    "UploadedFile",
    "UploadedRawFile",
    "UploadedEncryptedFile"
]

TIMESTAMP_PRECISION = 1000
FILENAME_LENGTH_PADDING = 6  # More than enough for almost every file system
MARK_SIZE = 1
ENCRYPTED_MARK = b'1'
UNENCRYPTED_MARK = b'0'

FILENAME_FOOTER_FORMAT = '{:0' + str(FILENAME_LENGTH_PADDING) + 'd}'


def generate_filename() -> str:
    """
    Generates a filename. Currently the upload date timestamp in milliseconds is
    used.
    """
    return str(int(time.time() * TIMESTAMP_PRECISION))


def read_file(filename: str) -> 'UploadedFile':
    """
    Reads a file stored in the server and removes its header indicating
    whether it is encrypted. If it is encrypted an UploadedEncryptedFile
    is returned for further decryption, else an UploadedRawFile is returned.

    :param filename: Filename of the file stored in-server.
    :return: Object representation of the binary file.
    """
    with open(filename, 'rb') as f:
        raw_file = f.read()
    header, payload = raw_file[:MARK_SIZE], raw_file[MARK_SIZE:]
    if header == ENCRYPTED_MARK:
        return UploadedEncryptedFile(
            filename=filename,
            data=payload
        )
    else:
        return UploadedRawFile.from_payload(payload, filename)


def file_from_file_storage(file: FileStorage) -> 'UploadedRawFile':
    """
    Converts a Flask FileStorage, which represents a file being uploaded
    into an UploadedRawFile for storage in-server.

    :param file: FileStorage being uploaded.
    :return: Object representation of the binary file.
    """
    filename = generate_filename()
    return UploadedRawFile(
        data=file.stream.read(),
        original_filename=file.filename.encode('utf-8'),
        filename=filename
    )


class UploadedFile:
    """
    Represents a file stored in-server. It should not be directly instanced,
    instead all of its subclasses implement the file property, which returns
    the binary representation of the file to be stored.
    """
    __slots__ = ('filename', 'data')

    def __init__(self, filename: str, data: bytes):
        self.filename = filename
        self.data = data

    @staticmethod
    def read(filename: str) -> 'UploadedFile':
        return read_file(filename)

    @staticmethod
    def from_file_storage(file: FileStorage) -> 'UploadedRawFile':
        return file_from_file_storage(file)

    @property
    def file(self) -> bytes:
        raise NotImplementedError

    @property
    def original_filename(self) -> str:
        raise NotImplementedError

    def is_encrypted(self) -> bool:
        return isinstance(self, UploadedEncryptedFile)

    def encrypt(self, key: bytes) -> 'UploadedFile':
        raise NotImplementedError

    def decrypt(self, key: bytes) -> 'UploadedFile':
        raise NotImplementedError

    def save(self, folder: str) -> None:
        """
        Saves the current file object in-server.

        :param folder: Folder on which the file should be saved.
        :return:
        """
        full_filename = os.path.join(folder, self.filename)
        with open(full_filename, 'wb+') as f:
            f.write(self.file)


class UploadedRawFile(UploadedFile):
    __slots__ = ('_original_filename',)

    def __init__(self, filename: str, data: bytes, original_filename: str):
        super().__init__(filename, data)
        self._original_filename = original_filename

    @property
    def file(self) -> bytes:
        return b''.join([
            UNENCRYPTED_MARK,
            self.payload
        ])

    @property
    def original_filename(self) -> str:
        return self._original_filename

    @property
    def payload(self) -> bytes:
        """
        Returns the payload of the current object, which is the raw file data
        and file metadata without the outer header indicating whether its
        encrypted.
        :return: Raw file content followed by a footer with its filename and
                 the base 10 representation of the filename length in the last
                 6 bytes.
        """
        filename_length = len(self.original_filename)
        return b''.join([
            self.data,
            self.original_filename,
            FILENAME_FOOTER_FORMAT.format(filename_length).encode('utf-8'),
        ])

    @classmethod
    def from_payload(cls, payload: bytes, filename: str) -> 'UploadedRawFile':
        """
        Splits a binary payload back into an UploadedRawFile object.

        :param payload: Binary payload including a filename footer.
        :param filename: Filename of the file stored in-server.
        :return: Object representation of the binary file.
        """
        filename_length = int(payload[-FILENAME_LENGTH_PADDING:])
        return cls(
            data=payload[:-(FILENAME_LENGTH_PADDING + filename_length)],
            original_filename=payload[
                              -(FILENAME_LENGTH_PADDING + filename_length)
                              :-FILENAME_LENGTH_PADDING
                              ].decode('utf-8'),
            filename=filename
        )

    def encrypt(self, key: bytes) -> 'UploadedEncryptedFile':
        """
        Encrypts the current file with the given key, returning an
        UploadedEncryptedFile.

        :param key: Encryption key.
        :return: Object representation of the encrypted file.
        """
        encrypted_payload = Encryptor(key).encrypt(self.payload)
        return UploadedEncryptedFile(
            filename=self.filename,
            data=encrypted_payload
        )

    def decrypt(self, key: bytes) -> 'UploadedFile':
        raise TypeError("File not encrypted.")


class UploadedEncryptedFile(UploadedFile):
    __slots__ = ('data',)

    def __init__(self, filename: str, data: bytes):
        super().__init__(filename, data)
        self.data = data

    @property
    def file(self) -> bytes:
        return b''.join([
            ENCRYPTED_MARK,
            self.data
        ])

    @property
    def original_filename(self) -> str:
        raise TypeError("Cannot read encrypted filename.")

    def encrypt(self, key: bytes) -> 'UploadedFile':
        raise TypeError("File already encrypted.")

    def decrypt(self, key: bytes) -> UploadedRawFile:
        """
        Decrypts the current file with the given key, returning an
        UploadedRawFile.

        :param key: Decryption key.
        :return: Object representation of the decrypted file.
        """
        decrypted_payload = Encryptor(key).decrypt(self.data)
        return UploadedRawFile.from_payload(decrypted_payload, self.filename)
