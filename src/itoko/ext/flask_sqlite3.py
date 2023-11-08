"""
Copy-pasted from http://flask.pocoo.org/docs/1.0/extensiondev/
"""
import sqlite3
from flask import current_app, g

__all__ = ["SQLite3"]


def _make_dicts(cursor: sqlite3.Cursor, row: sqlite3.Row):
    return {
        cursor.description[idx][0]: value
        for idx, value in enumerate(row)
    }


class SQLite3(object):
    """ SQLite 3 connector for Flask applications. """

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.config.setdefault('SQLITE3_DATABASE', ':memory:')
        app.teardown_appcontext(self.teardown)

    def connect(self):
        return sqlite3.connect(
            (self.app or current_app).config['SQLITE3_DATABASE']
        )

    def teardown(self, exception):
        if hasattr(g, '_sqlite3_db'):
            g._sqlite3_db.close()

    @property
    def connection(self):
        if not hasattr(g, '_sqlite3_db'):
            g._sqlite3_db = self.connect()
        return g._sqlite3_db

    def query(self, query: str, args=(), one=False):
        cur = self.connection.execute(query, args)
        rv = cur.fetchall()
        dv = [_make_dicts(cur, r) for r in rv]
        cur.close()
        return (dv[0] if dv else None) if one else dv

    def execute(self, query: str, args=()):
        self.connection.execute(query, args)
        self.connection.commit()
