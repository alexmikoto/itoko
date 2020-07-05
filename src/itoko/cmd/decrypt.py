import argparse
import sys
from itoko.fs.format.v1 import ItokoV1FormatReader
from itoko.fs.format.v2 import ItokoV2FormatReader

readers = [
    ItokoV1FormatReader(),
    ItokoV2FormatReader(),
]


def decrypt(filename: str, key: str) -> None:
    with open(filename, "rb") as f:
        data = f.read()
        for reader in readers:
            if reader.complies(data):
                eff = reader.read(filename, data)
                ff = eff.decrypt(key.encode("utf-8"))
                sys.stdout.buffer.write(ff.payload)


def main():
    parser = argparse.ArgumentParser(description='Decrypt a file.')
    parser.add_argument(
        'filename', metavar='FILE', type=str, help='file to read'
    )
    parser.add_argument('key', metavar="kEY", type=str, help='decryption key')
    args = parser.parse_args()
    decrypt(args.filename, args.key)


if __name__ == '__main__':
    main()
