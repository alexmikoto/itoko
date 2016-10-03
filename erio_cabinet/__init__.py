import magic
import os
import tempfile
from io import BytesIO
from urllib.parse import quote

from flask import abort, Flask, flash, jsonify, make_response, redirect, request, render_template, send_file, url_for

from erio_cabinet.crypto import AESCipher, AESCipherException, generate_key
from erio_cabinet.files import concat_file, split_file, generate_filename, mark_file, unmark_file
from erio_cabinet.util import request_wants_json, BadFileException

ATTACHMENT_MIMETYPES = ['text/html']

app = Flask(__name__, static_folder='static', static_url_path='')
app.config.update(
    SITE_URL='http://localhost:5000',
    UPLOAD_FOLDER=tempfile.gettempdir(),
    MAX_CONTENT_LENGTH=256 * 1024 * 1024,
    SECRET_KEY=os.urandom(32)
)
app.config.from_envvar('ERIO_CABINET_CONFIG', silent=True)

# Make the folder if it doesn't exist
os.makedirs(os.path.dirname(app.config['UPLOAD_FOLDER']), exist_ok=True)


@app.route('/')
def home_page():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part', category='error')
        return redirect(url_for('home_page'))

    file = request.files['file']
    encrypt = request.form.get('encrypt')
    if encrypt:
        encrypt = encrypt in ['1', 'true', 'on']  # Hacky way to check if the string contained is a true value.

    if file.filename == '':
        flash('No file selected', category='error')
        return redirect(url_for('home_page'))

    file = concat_file(file)

    if encrypt:
        key = generate_key()
        cipher = AESCipher(key)
        file = cipher.encrypt(file)
        file = mark_file(file, True)
    else:
        file = mark_file(file, False)

    filename = generate_filename()
    full_filename = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    with open(full_filename, 'wb+') as f:
        f.write(file)

    if encrypt:
        file_url = '{site_url}/u/{filename}?key={key}'.format(site_url=app.config['SITE_URL'],
                                                              filename=filename, key=key.decode('utf-8'))
    else:
        file_url = '{site_url}/u/{filename}'.format(site_url=app.config['SITE_URL'], filename=filename)

    if request_wants_json():
        return jsonify(url=file_url)
    return render_template('upload_successful.html', file_url=file_url)


@app.route('/u/<filename>')
def serve_file(filename):
    full_filename = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    key = request.args.get('key')

    if not os.path.exists(full_filename):
        abort(404)
        return

    with open(full_filename, 'rb') as f:
        file, encrypted = unmark_file(f.read())

    if encrypted:
        try:
            cipher = AESCipher((key or '').encode('utf-8'))  # Put an empty key if none was provided
            file = cipher.decrypt(file)
        except AESCipherException:
            abort(403)
            return

    file, filename = split_file(file)
    mimetype = magic.from_buffer(file, mime=True)
    io = BytesIO(file)
    response = make_response(send_file(io, mimetype=mimetype))

    # Add filename, set as attachment if not allowed inline
    if mimetype in ATTACHMENT_MIMETYPES:
        response.headers['Content-Disposition'] = 'attachment; filename="{filename}"; filename*=UTF-8\'\'{filename}' \
                                                      .format(filename=quote(filename))
    else:
        response.headers['Content-Disposition'] = 'inline; filename="{filename}"; filename*=UTF-8\'\'{filename}' \
                                                      .format(filename=quote(filename))
    return response


if __name__ == '__main__':
    app.debug = True  # Assume debugging
    app.run()
