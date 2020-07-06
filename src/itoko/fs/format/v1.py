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
"""
import struct

from itoko.crypto.suite.aesv1 import AESv1Suite
from itoko.fs.format import FormatReader, FormatFile

__all__ = ["ItokoV1FormatReader", "ItokoV1FormatFile"]


class ItokoV1FormatReader(FormatReader):
    HEADER_FORMAT = "!c"
    HEADER_SIZE = struct.calcsize("!c")
    FOOTER_FORMAT = "!6s"
    FOOTER_SIZE = struct.calcsize("!6s")

    ENCRYPTED_HEADER = b"1"
    UNENCRYPTED_HEADER = b"0"
    FILENAME_FOOTER_FORMAT = "{:06d}"

    def complies(self, payload: bytes) -> bool:
        header = payload[: self.HEADER_SIZE]
        return header in (self.ENCRYPTED_HEADER, self.UNENCRYPTED_HEADER)

    def read(self, filename: str, payload: bytes) -> "FormatFile":
        if self.complies(payload):
            return ItokoV1FormatFile.read(filename, payload)


class ItokoV1FormatFile(FormatFile):
    @classmethod
    def read(cls, filename: str, payload: bytes) -> "ItokoV1FormatFile":
        """
        Splits a binary payload back into an ItokoV1FormatFile object.

        :param filename: Filename of the file stored in-server.
        :param payload: Binary payload including a filename footer.
        :return: Object representation of the binary file.
        """
        fr = ItokoV1FormatReader  # Gets tiring on the eyes
        header = payload[: fr.HEADER_SIZE]
        if header == fr.ENCRYPTED_HEADER:
            return cls._read_enc(filename, payload)
        else:
            return cls._read_dec(filename, payload)

    @classmethod
    def _read_enc(cls, filename: str, payload: bytes) -> "ItokoV1FormatFile":
        fr = ItokoV1FormatReader  # And also gets tiring on the eyes
        header, data = payload[: fr.HEADER_SIZE], payload[fr.HEADER_SIZE:]
        return cls(
            payload=data,
            fs_filename=filename,
            is_encrypted=True,
            filename=None,
            mime_type=None,
        )

    @classmethod
    def _read_dec(cls, filename: str, payload: bytes) -> "ItokoV1FormatFile":
        fr = ItokoV1FormatReader  # Also gets tiring on the eyes
        header, data, footer = (
            payload[: fr.HEADER_SIZE],
            payload[fr.HEADER_SIZE: -fr.FOOTER_SIZE],
            payload[-fr.FOOTER_SIZE:],
        )
        # We still need to read the filename based on the footer
        filename_size, = struct.unpack(fr.FOOTER_FORMAT, footer)
        filename_size = int(filename_size.decode("utf-8"))
        file_data, r_filename = data[:-filename_size], data[-filename_size:]
        r_filename = r_filename.decode("utf-8")
        # Got all data
        return cls(
            payload=file_data,
            fs_filename=filename,
            is_encrypted=False,
            filename=r_filename,
            mime_type=None,
        )

    @property
    def file(self) -> bytes:
        """
        Returns the binary representation of the current object, which is the
        header plus raw file data and file metadata. V1 format does not store
        mime_type.
        :return: Header followed by raw file content, followed by a footer with
                 its filename and the base 10 representation of the filename
                 length in the last 6 bytes.
        """
        fr = ItokoV1FormatReader  # Just because it gets tiring on the eyes too
        header = fr.UNENCRYPTED_HEADER
        filename_bytes = self._filename.encode("utf-8")
        footer = fr.FILENAME_FOOTER_FORMAT.format(len(filename_bytes)).format(
            "utf-8"
        )
        footer = struct.pack(fr.FOOTER_FORMAT, footer)
        return b"".join([header, self._payload, filename_bytes, footer])

    def _encryptor(self, key: bytes) -> "ItokoV1FormatFile":
        encrypted_payload = AESv1Suite(key).encrypt(self._payload)
        return ItokoV1FormatFile(
            payload=encrypted_payload,
            fs_filename=self._fs_filename,
            is_encrypted=True,
            filename=None,
            mime_type=None,
        )

    def _decryptor(self, key: bytes) -> "ItokoV1FormatFile":
        decrypted_payload = AESv1Suite(key).decrypt(self._payload)
        # Far easier to just reuse the previous reader
        return self._read_dec(
            self._fs_filename,
            ItokoV1FormatReader.UNENCRYPTED_HEADER + decrypted_payload,
        )
