from flask import Flask, render_template

from crypto.aes import AESCipher

app = Flask(__name__, static_folder='static')


@app.route('/')
def home_page():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    return render_template('upload_successful.html')


if __name__ == '__main__':
    app.run()
