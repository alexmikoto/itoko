__all__ = ["InvalidKeyLengthError"]


class InvalidKeyLengthError(Exception):
    """
    Raised when the specified key length is not supported by the current key
    derivation suite.
    """
