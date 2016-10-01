import os
import tempfile
import time
import base64

from io import BytesIO
from flask import abort, Flask, flash, redirect, request, render_template, send_file, url_for

from crypto.aes_cipher import AESCipher

app = Flask(__name__, static_folder='static')
app.config.update(
    SITE_URL='http://localhost:5000',
    UPLOAD_FOLDER=tempfile.gettempdir(),
    MAX_CONTENT_LENGTH=256 * 1024 * 1024,
    SECRET_KEY=os.urandom(32)
)
app.config.from_pyfile('config.cfg', silent=True)


@app.route('/')
def home_page():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('home_page'))
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
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

    if not os.path.exists(full_filename) or not key:
        abort(404)
        return

    key = key.encode('utf-8')

    cipher = AESCipher(key)

    with open(full_filename, 'rb') as f:
        try:
            decrypted = cipher.decrypt(f.read())
            io = BytesIO(decrypted)
            return send_file(io)
        except IOError:
            abort(404)


if __name__ == '__main__':
    app.run()
