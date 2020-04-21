class FSStorage:
    """

    """

    def __init__(self) -> None:
        pass

    def read_file(self, filename: str) -> 'UploadedFile':
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

    def file_from_file_storage(self, file: FileStorage) -> 'UploadedRawFile':
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
