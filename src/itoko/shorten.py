from typing import Optional

from itoko.db import db


def shorten_filename(filename: str) -> str:
    db.execute("INSERT INTO shortened (filename) VALUES (?)", (filename,))
    result = db.query(
        "SELECT short_name FROM shortened WHERE filename = ?",
        (filename,),
        one=True,
    )
    short_name = result["short_name"]
    return f"{short_name:03d}"


def find_shortened(short_name: str) -> Optional[str]:
    result = db.query(
        "SELECT filename FROM shortened WHERE short_name = ?",
        (short_name,),
        one=True,
    )
    if not result:
        return None
    return result["filename"]
