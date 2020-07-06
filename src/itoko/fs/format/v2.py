"""
Handles the binary protocol for files.

Header layout:
typedef struct header {
    uint8_t version;
    uint8_t flags;
    uint16_t filename_length;
    uint16_t mime_type_length;
    uint16_t padding;
};

The flags field is a bit field with the current bits currently in use:
1: No use
2: No use
3: No use
4: No use
5: No use
6: No use
7: Encrypted flag
8: No use

If the encrypted flag is set, the filename_length and mime_type_length will be
assume to be set to zero.

In the case of a non-encrypted file, the next filename_length bytes following
the header will be expected to contain the filename as a character sequence,
and the following mime_type_length will be expected to contain the MIME type
as a character sequence.
"""
import struct

from itoko.crypto.suite.aesv2 import AESv2Suite
from itoko.fs.format import FormatReader, FormatFile

__all__ = ["ItokoV2FormatReader", "ItokoV2FormatFile"]


class ItokoV2FormatReader(FormatReader):
    HEADER_FORMAT = "!BBHH2x"
    HEADER_SIZE = struct.calcsize("!BBHH2x")

    # In V1 the first byte will always be 0x30 or 0x31, so every number up to
    # that is safe
    VERSION = 0x2
    ENCRYPTED_FLAG = 0b0000_0010

    def complies(self, payload: bytes) -> bool:
        header = payload[: struct.calcsize(self.HEADER_FORMAT)]
        version, _, _, _ = struct.unpack(self.HEADER_FORMAT, header)
        return version == self.VERSION

    def read(self, filename: str, payload: bytes) -> "FormatFile":
        if self.complies(payload):
            return ItokoV2FormatFile.read(filename, payload)


class ItokoV2FormatFile(FormatFile):
    @classmethod
    def read(cls, filename: str, payload: bytes) -> "ItokoV2FormatFile":
        """
        Splits a binary payload back into an ItokoV2FormatFile object.

        :param filename: Filename of the file stored in-server.
        :param payload: Binary payload including a filename footer.
        :return: Object representation of the binary file.
        """
        fr = ItokoV2FormatReader  # Just because it gets tiring on the eyes
        header, data = payload[: fr.HEADER_SIZE], payload[fr.HEADER_SIZE:]
        # Parse header
        version, flags, fn_len, mt_len = struct.unpack(
            fr.HEADER_FORMAT, header
        )
        # Parse flags, due to python behavior we can just wrap in bool()
        is_encrypted = bool(flags & fr.ENCRYPTED_FLAG)
        # Deal with enc/dec
        if is_encrypted:
            return cls(
                payload=data,
                fs_filename=filename,
                is_encrypted=True,
                filename=None,
                mime_type=None,
            )
        else:
            fn, mt, file_data = (
                data[:fn_len].decode("utf-8"),
                data[fn_len: fn_len + mt_len].decode("utf-8"),
                data[fn_len + mt_len:],
            )
            return cls(
                payload=file_data,
                fs_filename=filename,
                is_encrypted=False,
                filename=fn,
                mime_type=mt,
            )

    @property
    def file(self) -> bytes:
        """
        Returns the binary representation of the current object, which is the
        header plus file metadata plus file data.

        :return: Header followed by raw file content.
        """
        fr = ItokoV2FormatReader  # Just because it gets tiring on the eyes too
        version = fr.VERSION
        if self._is_encrypted:
            flags = 0x0 | fr.ENCRYPTED_FLAG
            fn_len = 0
            mt_len = 0
        else:
            flags = 0x0
            fn_len = len(self.filename)
            mt_len = len(self.mime_type)
        header = struct.pack(fr.HEADER_FORMAT, version, flags, fn_len, mt_len)
        if self._is_encrypted:
            return b"".join([header, self._payload])
        else:
            return b"".join([
                header,
                self._filename.encode("utf-8"),
                self._mime_type.encode("utf-8"),
                self._payload,
            ])

    def _encryptor(self, key: bytes) -> "ItokoV2FormatFile":
        """
        Encrypts the current file with the given key, returning an
        UploadedEncryptedFile.

        :param key: Encryption key.
        :return: Object representation of the encrypted file.
        """
        # We encrypt the file + headers to ease parsing when decrypting
        encrypted_payload = AESv2Suite(key).encrypt(self.file)
        return ItokoV2FormatFile(
            payload=encrypted_payload,
            fs_filename=self._fs_filename,
            is_encrypted=True,
            filename=None,
            mime_type=None,
        )

    def _decryptor(self, key: bytes) -> "ItokoV2FormatFile":
        decrypted_payload = AESv2Suite(key).decrypt(self._payload)
        # This way we just feed the file to the read() function
        return self.read(self._fs_filename, decrypted_payload)
