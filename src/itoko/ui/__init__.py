from flask import Blueprint, render_template

__all__ = ["ui_blueprint"]

ui_blueprint = Blueprint(
    "ui",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path=""
)


@ui_blueprint.route("/")
def home_page():
    return render_template("index.html")
