__all__ = ["InvalidKeyLengthError", "DecryptionError"]


class InvalidKeyLengthError(Exception):
    """
    Raised when the specified key length is not supported by the current key
    derivation suite.
    """


class DecryptionError(Exception):
    """
    Raised when ciphertext decryption fails. Generally caused by the HMAC
    function failing to authenticate the given key.
    """
