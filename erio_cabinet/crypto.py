import os
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.hmac import HMAC
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


KEY_LENGTH = 32
SALT_SIZE = 16
BLOCK_SIZE = 16
ITERATION_COUNT = 100000

backend = default_backend()


class AESCipher:
    def __init__(self, key):
        self.key = key

    def encrypt(self, plaintext):
        salt = os.urandom(SALT_SIZE)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256,
            length=2*KEY_LENGTH,
            salt=salt,
            iterations=ITERATION_COUNT,
            backend=backend
        )
        derived_key = kdf.derive(self.key)
        cipher_key, hmac_key = derived_key[:KEY_LENGTH], derived_key[-KEY_LENGTH:]
        nonce = os.urandom(BLOCK_SIZE)
        cipher = Cipher(algorithms.AES(cipher_key), modes.CTR(nonce), backend=backend)
        encryptor = cipher.encryptor()

        # Encrypted
        encrypted = encryptor.update(plaintext) + encryptor.finalize()

        # Concat nonce
        encrypted = nonce + encrypted

        # MAC over encrypted text
        h = HMAC(hmac_key, hashes.SHA256(), backend=backend)
        h.update(encrypted)
        hmac = h.finalize()

        # Return concat
        return b''.join([encrypted, hmac, salt])

    def decrypt(self, encrypted):
        encrypted, hmac, salt = encrypted[:-(SALT_SIZE + hashes.SHA256.digest_size)],\
                                encrypted[-(SALT_SIZE + hashes.SHA256.digest_size): -SALT_SIZE],\
                                encrypted[-SALT_SIZE:]

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256,
            length=2*KEY_LENGTH,
            salt=salt,
            iterations=ITERATION_COUNT,
            backend=backend
        )
        derived_key = kdf.derive(self.key)
        cipher_key, hmac_key = derived_key[:KEY_LENGTH], derived_key[-KEY_LENGTH:]

        # Check MAC over encrypted text
        h = HMAC(hmac_key, hashes.SHA256(), backend=backend)
        h.update(encrypted)
        h.verify(hmac)

        nonce, encrypted = encrypted[:BLOCK_SIZE], encrypted[BLOCK_SIZE:]

        cipher = Cipher(algorithms.AES(cipher_key), modes.CTR(nonce), backend=backend)
        decryptor = cipher.decryptor()

        # Decrypt
        return decryptor.update(encrypted) + decryptor.finalize()
