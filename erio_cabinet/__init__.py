import base64
import magic
import os
import tempfile
import time
from io import BytesIO

from flask import abort, Flask, flash, make_response, redirect, request, render_template, send_file, url_for

from erio_cabinet.crypto import AESCipher, AESCipherException

ATTACHMENT_MIMETYPES = ['text/html']

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

    key = base64.urlsafe_b64encode(os.urandom(18))

    filename = file.filename
    timestamp = int(time.time() * 10000000)

    cipher = AESCipher(key)
    # Save the original filename in the end of the encrypted file
    encrypted = cipher.encrypt(b''.join([file.read(),
                                         filename.encode('utf-8'),
                                         '{:06d}'.format(len(filename)).encode('utf-8')]))

    new_filename = str(timestamp)
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

            # Split up encrypted file and filename
            filename_length = int(decrypted[-6:])
            decrypted, filename = decrypted[:-(6+filename_length)], decrypted[-(6+filename_length):-6]

            # Make filename a string
            filename = filename.decode('utf-8')

            # Guess MIME type
            mimetype = magic.from_buffer(decrypted, mime=True)

            io = BytesIO(decrypted)
            response = make_response(send_file(io, mimetype=mimetype))

            # Add filename, set as attachment if not allowed inline
            if mimetype in ATTACHMENT_MIMETYPES:
                response.headers['Content-Disposition'] = 'attachment; filename="{filename}"'.format(filename=filename)
            else:
                response.headers['Content-Disposition'] = 'inline; filename="{filename}"'.format(filename=filename)
            return response
        except AESCipherException:
            abort(403)


if __name__ == '__main__':
    app.run()
