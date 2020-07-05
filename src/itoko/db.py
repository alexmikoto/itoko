from itoko.ext.flask_sqlite3 import SQLite3

__all__ = ["db", "init_db"]

db = SQLite3()


def init_db():
    db.execute("""
    CREATE TABLE IF NOT EXISTS shortened (
      short_name INTEGER PRIMARY KEY,
      filename TEXT UNIQUE NOT NULL
    )
    """)
