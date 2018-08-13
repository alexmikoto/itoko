from urllib.parse import quote

from flask import request

ATTACHMENT_MIMETYPES = ['text/html']


class BadFileError(Exception):
    pass


def request_wants_json():
    best = request.accept_mimetypes.best_match([
        'application/json', 'text/html'
    ])
    return best == 'application/json' and request.accept_mimetypes[best] > request.accept_mimetypes['text/html']


def get_content_disposition(filename: str, mimetype: str) -> str:
    escaped = quote(filename)
    if mimetype in ATTACHMENT_MIMETYPES:
        return f'attachment; filename="{escaped}"; filename*=UTF-8\'\'{escaped}'
    else:
        return f'inline; filename="{escaped}"; filename*=UTF-8\'\'{escaped}'
