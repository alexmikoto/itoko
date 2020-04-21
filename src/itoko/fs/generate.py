import os
import time
import base64

TIMESTAMP_PRECISION = 1000


def generate_key() -> bytes:
    """
    Generates a random key by passing /dev/urandom through URL-safe base64
    encoding.
    """
    return base64.urlsafe_b64encode(os.urandom(18))


def generate_filename() -> str:
    """
    Generates a filename. Currently the upload date timestamp in milliseconds is
    used.
    """
    return str(int(time.time() * TIMESTAMP_PRECISION))
