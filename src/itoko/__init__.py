import os
import tempfile

import toml
from flask import Flask

from itoko.imp import import_object
from itoko.db import db, init_db
from itoko.api import api_blueprint
from itoko.ui import ui_blueprint

__version__ = "0.3.4"


def make_app():
    app = Flask(__name__)
    # Set default configuration values
    app.config.update(
        MAX_CONTENT_LENGTH=256 * 1024 * 1024,
        SECRET_KEY=os.urandom(32),
        SQLITE3_DATABASE=os.path.join(tempfile.gettempdir(), "test.db"),
        ITOKO_STORAGE=dict(
            temporary_folder=tempfile.gettempdir(),
            permanent_folder=tempfile.gettempdir(),
            writer="itoko.fs.format.v2:ItokoV2FormatFile",
            readers=[
                "itoko.fs.format.v1:ItokoV1FormatReader",
                "itoko.fs.format.v2:ItokoV2FormatReader",
            ]
        ),
        ITOKO_UI=dict(
            abuse_email="abuse@itoko.moe",
        ),
    )
    if os.getenv("ITOKO_CONFIG"):
        cfg = toml.load(os.getenv("ITOKO_CONFIG"))
        app.config.update(cfg)

    # Make the uploads folder if it doesn't exist
    os.makedirs(app.config["ITOKO_STORAGE"]["temporary_folder"], exist_ok=True)

    # Make the permanent uploads folder if it doesn't exist
    os.makedirs(app.config["ITOKO_STORAGE"]["permanent_folder"], exist_ok=True)

    app.config["ITOKO_STORAGE"]["writer"] = import_object(
        app.config["ITOKO_STORAGE"]["writer"]
    )
    app.config["ITOKO_STORAGE"]["readers"] = [
        import_object(reader)
        for reader in app.config["ITOKO_STORAGE"]["readers"]
    ]

    # Add sqlite3 extension
    db.init_app(app)

    # Initialize database if empty
    with app.app_context():
        init_db()

    # Register routes
    app.register_blueprint(api_blueprint)
    app.register_blueprint(ui_blueprint)

    return app


def main():
    app = make_app()
    app.debug = True  # Assume debugging
    app.run()


if __name__ == "__main__":
    main()
