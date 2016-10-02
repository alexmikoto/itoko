import time

from werkzeug.datastructures import FileStorage

FILENAME_LENGTH_PADDING = 6


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
    return str(int(time.time() * 10000000))
