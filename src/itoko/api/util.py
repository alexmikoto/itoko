from urllib.parse import quote

from flask import request

__all__ = ["request_wants_json", "get_content_disposition"]

INLINE_MIMETYPES = [
    "application/json",
    "application/mp4",
    "application/pdf",
    "audio/aac",
    "audio/flac",
    "audio/x-flac",
    "audio/midi",
    "audio/x-midi",
    "audio/mp4",
    "audio/mpeg",
    "audio/ogg",
    "audio/opus",
    "audio/wav",
    "audio/webm",
    "audio/3gpp",
    "audio/3gpp2",
    "image/bmp",
    "image/gif",
    "image/jpeg",
    "image/png",
    "image/tiff",
    "image/webp",
    "text/csv",
    "text/csv-schema",
    "text/plain",
    "video/x-msvideo",
    "video/mp4",
    "video/mpeg",
    "video/ogg",
    "video/mp2t",
    "video/webm",
    "video/3gpp",
    "video/3gpp2",
]


def request_wants_json():
    """
    Returns whether the current Flask request is expecting an application/json
    response.

    :return: Boolean indicating application/json acceptance.
    """
    best = request.accept_mimetypes.best_match(
        ["application/json", "text/html"]
    )
    return (
        best == "application/json"
        and (
            request.accept_mimetypes[best]
            > request.accept_mimetypes["text/html"]
        )
    )


def get_content_disposition(filename: str, mimetype: str) -> str:
    """
    Makes a Content-Disposition HTTP header based a filename and a MIME type.
    If the file is allowed inline it will be sent inline, however any other
    file type will be sent as an attachment to avoid an XSS vector.

    :param filename: Filename to send in the header.
    :param mimetype: MIME type of the file.
    :return:
    """
    escaped = quote(filename)
    if mimetype in INLINE_MIMETYPES:
        return f"inline; filename=\"{escaped}\"; filename*=UTF-8''{escaped}"
    else:
        return (
            f"attachment; filename=\"{escaped}\"; filename*=UTF-8''{escaped}"
        )
