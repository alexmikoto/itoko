import argparse
import magic
from itoko.fs.format.v2 import ItokoV2FormatFile


def encrypt(filename: str, key: str) -> None:
    with open(filename, "rb") as f:
        data = f.read()
        ff = ItokoV2FormatFile(
            payload=data,
            fs_filename=None,
            is_encrypted=False,
            filename=filename,
            mime_type=magic.from_buffer(data, mime=True)
        )
        eff = ff.encrypt(key.encode("utf-8"))
        print(eff.file)


def main():
    parser = argparse.ArgumentParser(description='Encrypt a file.')
    parser.add_argument(
        'filename', metavar='FILE', type=str, help='file to read'
    )
    parser.add_argument('key', metavar="kEY", type=str, help='encryption key')
    args = parser.parse_args()
    encrypt(args.filename, args.key)


if __name__ == '__main__':
    main()
