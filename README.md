# itoko
###### File hosting for very special people.

## Summary
Allows plaintext file upload and download,
data is physically stored ciphered in AES-256. Uses a SHA-256 HMAC for
verification.

## Specification
itoko stores any uploaded file with an additional header containing file
metadata.

All file have the following header structure prepended:
```c
struct header {
    uint8_t version;
    uint8_t flags;
    char[6] r1;  /* reserved */
};
```

The `version` field is always `0x01` in the current revision. The `flags` field
is a bit field. Currently only the last bit is in use as a boolean flag
indicating whether the file is encrypted or not. In the case of an encrypted
file the flags field will always contain `0x01`.

In the case of an encrypted file an additional header structure is appended 
right after the first header, which has the following structure:
```c
struct encrypted_header {
    uint16_t kdf_suite;
    uint16_t crypto_suite;
    uint32_t key_length;
    uint64_t salt;
    uint64_t iv;
};
```

The `key_suite` field contains an enumerated value indicating the key derivation
suite used for the current file key derivation. A `key_suite` in itoko contains
a key derivation function of the form `KDF(key, salt) -> derived_key`, where the
`derived_key` output is a pseudo-random result of size `key_length` octets.
 
The `crypto_suite` field contains an enumerated value indicating the
cryptography suite used for the current file encryption. A `crypto_suite` in
itoko contains the following components:
- An encryption function of the form `C(message, key, iv) -> ciphertext`
- A decryption function of the form `D(ciphertext, key, iv) -> message`

Currently the following suites are available for key derivation:
- `0x0001`: `PBKDF2-HMAC(prf=SHA256, iterations=100000, ...)`. Supported key
  lengths are: 32, 64. Refered to as PBKDF for shortness in code.

And currently the following suites are available for encryption:
- `0x0001`: `AES256(mode=CTR, ...)+HMAC(hash=SHA256, ...)`. Supported key
  lengths are: 64. Due to the need of both an cipher key and an authentication
  key, this suite uses a double sized derived key. 

The `salt` field stores the salt value used for key derivation. The `iv` field
stores the initialization vector or nonce applied to the encryption algorithm.
