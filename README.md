# itoko
###### File hosting for very special people.

## Summary
Allows plaintext file upload and download,
data is physically stored ciphered in AES-256. Uses a SHA-256 HMAC for
verification.

## Specification
itoko stores any uploaded file with an additional header containing file
metadata.

In the current version, all file have the following header structure prepended:
```c
struct header {
    uint8_t version;
    uint8_t flags;
    uint16_t filename_length;
    uint16_t mime_type_length;
    uint16_t padding;
};
```

The `version` field is always `0x02` in the current revision. The `flags` field
is a bit field. Currently only the 7th bit is in use as a boolean flag
indicating whether the file is encrypted or not. In the case of an encrypted
file the flags field will always contain a set 7th bit.

In the case of an encrypted file an additional header structure is appended 
right after the first header, which has the following structure:
```c
struct crypto_header {
    uint16_t suite_id;
    uint16_t salt;
    uint32_t hmac;
};
```

The `suite_id` field contains an enumerated value indicating the cryptographic
suite used for the current file. A suite in itoko defines a function with the
form `encrypt(key, plaintext) -> ciphertext` and a function with the form
`decrypt(key, ciphertext) -> plaintext`. Each suite handles its own internal
procedure, including key derivation function and block cipher mode.

The `salt` field stores the salt value used for key derivation, the `hmac` field
the result of the validation function. As the nonce/iv must be validated in all
ciphers, it is not included in the crypto header and is instead prepended as the
first block in the validated ciphertext.

Currently the following suites are available:
- `0x0001`: `AES(len=256, mode=CTR, kdf=PBKDF2-HMAC(SHA256), iterations=100000, ...)`.
- `0x0002`: `AES(len=256, mode=CTR, kdf=PBKDF2-HMAC(SHA256), iterations=100000, ...)`.
            The difference between this suite and suite 1 is the binary format.
            Suite 1 does not use the new crypto header format.
