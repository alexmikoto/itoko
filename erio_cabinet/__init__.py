import base64
import magic
import os
import tempfile
import time
from io import BytesIO

from flask import abort, Flask, flash, redirect, request, render_template, send_file, url_for

from erio_cabinet.crypto import AESCipher, AESCipherException

app = Flask(__name__, static_folder='static', static_url_path='')
app.config.update(
    SITE_URL='http://localhost:5000',
    UPLOAD_FOLDER=tempfile.gettempdir(),
    MAX_CONTENT_LENGTH=256 * 1024 * 1024,
    SECRET_KEY=os.urandom(32)
)
app.config.from_envvar('ERIO_CABINET_CONFIG', silent=True)


@app.route('/')
def home_page():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part', category='error')
        return redirect(url_for('home_page'))
    file = request.files['file']
    if file.filename == '':
        flash('No file selected', category='error')
        return redirect(url_for('home_page'))

    key = base64.urlsafe_b64encode(os.urandom(16))

    cipher = AESCipher(key)
    encrypted = cipher.encrypt(file.read())

    filename, extension = os.path.splitext(file.filename)
    new_filename = str(time.time()) + extension

    full_filename = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)

    with open(full_filename, 'wb+') as f:
        f.write(encrypted)

    return render_template('upload_successful.html', site_url=app.config['SITE_URL'],
                           filename=new_filename, key=key.decode('utf-8'))


@app.route('/uploads/<filename>')
def serve_file(filename):
    full_filename = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    key = request.args.get('key')

    if not os.path.exists(full_filename):
        abort(404)
        return

    if not key:
        abort(403)
        return

    key = key.encode('utf-8')

    cipher = AESCipher(key)

    with open(full_filename, 'rb') as f:
        try:
            decrypted = cipher.decrypt(f.read())
            mimetype = magic.from_buffer(decrypted, mime=True)
            io = BytesIO(decrypted)
            return send_file(io, mimetype=mimetype)
        except AESCipherException:
            abort(403)


if __name__ == '__main__':
    app.run()
