from io import BytesIO

from flask import (
    Blueprint,
    current_app,
    abort,
    flash,
    jsonify,
    make_response,
    redirect,
    request,
    render_template,
    send_file,
    url_for,
)

from itoko.fs.storage import FSStorageType, FSStorage
from itoko.fs.generators import default_key_generator
from itoko.fs.format.v1 import ItokoV1FormatReader
from itoko.fs.format.v2 import ItokoV2FormatReader, ItokoV2FormatFile
from itoko.crypto.exc import DecryptionError
from itoko.api.util import request_wants_json, get_content_disposition
from itoko.shorten import shorten_filename, find_shortened

api_blueprint = Blueprint("api", __name__, template_folder="templates")


@api_blueprint.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        flash("No file part", category="error")
        return redirect(url_for("home_page"))

    st_cfg = current_app.config["ITOKO_STORAGE"]
    fs = FSStorage(
        temporary_folder=st_cfg["temporary_folder"],
        permanent_folder=st_cfg["permanent_folder"],
        readers=[
            reader() for reader in st_cfg["readers"]
        ]
    )

    r_file = request.files["file"]
    # Hacky way to check if the string contained is a true value.
    encrypt = request.form.get("encrypt") in ["1", "true", "on"]
    permanent = request.form.get("permanent") in ["1", "true", "on"]
    shorten = request.form.get("shorten") in ["1", "true", "on"]

    if r_file.filename == "":
        flash("No file selected", category="error")
        return redirect(url_for("home_page"))

    file = st_cfg["writer"](
        payload=r_file.stream.read(),
        filename=r_file.filename,
    )

    key = None  # silence annoying warnings
    if encrypt:
        key = default_key_generator()
        file = file.encrypt(key)

    if permanent:
        fst = FSStorageType.PERMANENT_STORAGE
    else:
        fst = FSStorageType.TEMPORARY_STORAGE

    fs.write(fst, file)

    # Use the set site URL if in config, else guess based on HOST header
    site_url = current_app.config.get("SITE_URL") or request.host_url[:-1]

    if encrypt:
        file_url = "{site_url}/u/{filename}?key={key}".format(
            site_url=site_url,
            filename=file.fs_filename,
            key=key.decode("utf-8"),
        )
    else:
        file_url = "{site_url}/u/{filename}".format(
            site_url=site_url, filename=file.fs_filename
        )

    if shorten:
        short_name = shorten_filename(file.fs_filename)
        if encrypt:
            short_url = "{site_url}/s/{short_name}?key={key}".format(
                site_url=site_url,
                short_name=short_name,
                key=key.decode("utf-8"),
            )
        else:
            short_url = "{site_url}/s/{short_name}".format(
                site_url=site_url, short_name=short_name
            )
    else:
        short_url = None

    if request_wants_json():
        return jsonify(url=file_url, short_url=short_url)

    # In the case we have to render an HTML response, render this ugly template
    # As it is not part of the UI proper and is a no JS workaround instead, this
    # template is not included in the UI folder.
    return render_template(
        "upload_successful.html",
        file_url=file_url,
        short_url=short_url,
    )


@api_blueprint.route("/u/<filename>")
@api_blueprint.route("/s/<short_filename>")
@api_blueprint.route("/b/<base64_filename>")
def serve_file(filename=None, short_filename=None, base64_filename=None):
    if not filename:
        if not short_filename:
            abort(404)
        filename = find_shortened(short_filename)
    if not filename:
        return abort(404)

    key = request.args.get('key')

    st_cfg = current_app.config["ITOKO_STORAGE"]
    fs = FSStorage(
        temporary_folder=st_cfg["temporary_folder"],
        permanent_folder=st_cfg["permanent_folder"],
        readers=[
            reader() for reader in st_cfg["readers"]
        ]
    )

    fst = fs.exists(filename)
    if not fst:
        return abort(404)

    file = fs.read(fst, filename)

    if file.is_encrypted:
        try:
            # Put an empty key if none was provided
            file = file.decrypt((key or "").encode("utf-8"))
        except DecryptionError:
            return abort(403)

    io = BytesIO(file.payload)
    response = make_response(send_file(io, mimetype=file.mime_type))

    # Add filename, set as attachment if not allowed inline
    response.headers["Content-Disposition"] = get_content_disposition(
        file.filename, file.mime_type
    )
    return response
