import time

from werkzeug.datastructures import FileStorage

# TIMESTAMP_PRECISION = 10000000
TIMESTAMP_PRECISION = 1000
FILENAME_LENGTH_PADDING = 6
MARK_SIZE = 1
ENCRYPTED_MARK = b'1'
UNENCRYPTED_MARK = b'0'


def concat_file(file: FileStorage) -> bytes:
    """ Returns the bytes content of a FileStorage object concatenated with its filename """
    filename = file.filename.encode('utf-8')
    return b''.join([file.read(), filename,
                     ('{:0' + str(FILENAME_LENGTH_PADDING) + 'd}').format(len(filename)).encode('utf-8')])


def split_file(raw_file: bytes) -> (bytes, str):
    """ Returns the bytes content of a concatenated file and its filename as a string """
    filename_length = int(raw_file[-6:])
    return raw_file[:-(FILENAME_LENGTH_PADDING + filename_length)],\
        raw_file[-(FILENAME_LENGTH_PADDING + filename_length):-FILENAME_LENGTH_PADDING].decode('utf-8')


def generate_filename() -> str:
    """ Generates a filename """
    # Use timestamp as filename
    return str(int(time.time() * TIMESTAMP_PRECISION))


def mark_file(file: bytes, encrypted: bool) -> bytes:
    """ Adds a magic number to the file marking it as encrypted or unencrypted """
    return (ENCRYPTED_MARK if encrypted else UNENCRYPTED_MARK) + file


def unmark_file(raw_file: bytes) -> (bytes, bool):
    """ Removes the magic number from the file, and returns the file and its encrypted status """
    magic_number, file = raw_file[:MARK_SIZE], raw_file[MARK_SIZE:]
    return file, magic_number == ENCRYPTED_MARK
