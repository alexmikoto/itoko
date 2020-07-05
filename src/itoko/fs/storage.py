import os
from enum import Enum
from typing import Optional, List

from itoko.fs.format import FormatReader, FormatFile

__all__ = ["FSStorageType", "FSStorage"]


class FSStorageType(Enum):
    TEMPORARY_STORAGE = 1
    PERMANENT_STORAGE = 2


class FSStorage:
    """
    Handles access to the external file system to store and retrieve files.
    """
    __slots__ = ("temporary_folder", "permanent_folder", "readers")

    temporary_folder: str
    permanent_folder: str
    readers: List[FormatReader]

    def __init__(
        self,
        temporary_folder: str,
        permanent_folder: str,
        readers: List[FormatReader],
    ) -> None:
        self.temporary_folder = temporary_folder
        self.permanent_folder = permanent_folder
        self.readers = readers

    def exists(self, filename: str) -> Optional[FSStorageType]:
        """
        Checks if a given filename exists in either storage folder. If it exists
        the storage folder where the file was found will be returned. In the
        opposite case, None will be returned.

        :param filename: Filename to search for.
        :return: Storage type where file was found or None.
        """
        perm = os.path.join(self.permanent_folder, filename)
        if os.path.exists(perm):
            return FSStorageType.PERMANENT_STORAGE
        temp = os.path.join(self.temporary_folder, filename)
        if os.path.exists(temp):
            return FSStorageType.TEMPORARY_STORAGE
        return None

    def read(self, st: FSStorageType, filename: str) -> FormatFile:
        """
        Reads a file stored in the server and attempts to parse it with the
        available readers. If the file complies with any reader, a FormatFile
        representation of it will be returned.

        :param st: Storage type to probe.
        :param filename: Filename of the file stored in-server.
        :return: Object representation of the binary file.
        """
        if st == FSStorageType.PERMANENT_STORAGE:
            path = os.path.join(self.permanent_folder, filename)
        elif st == FSStorageType.TEMPORARY_STORAGE:
            path = os.path.join(self.temporary_folder, filename)
        else:
            raise TypeError("Invalid storage type provided.")

        with open(path, "rb") as f:
            payload = f.read()

        for reader in self.readers:
            if reader.complies(payload):
                return reader.read(filename, payload)

        # We have a file, but can't parse it so pretend it's not there
        raise FileNotFoundError

    def write(self, st: FSStorageType, file: FormatFile) -> None:
        """
        Converts a Flask FileStorage, which represents a file being uploaded
        into an UploadedRawFile for storage in-server.

        :param st: Storage type to upload to.
        :param file: FileStorage being uploaded.
        :return: Object representation of the binary file.
        """
        if st == FSStorageType.PERMANENT_STORAGE:
            path = os.path.join(self.permanent_folder, file.fs_filename)
        elif st == FSStorageType.TEMPORARY_STORAGE:
            path = os.path.join(self.temporary_folder, file.fs_filename)
        else:
            raise TypeError("Invalid storage type provided.")

        with open(path, "wb+") as f:
            f.write(file.file)
