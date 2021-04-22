from flask import Flask, render_template, request, send_file, redirect, session
import os
import sys
import json
from flask_fontawesome import FontAwesome
import zipfile

app = Flask(__name__)

fa = FontAwesome(app)


@app.route('/')
def hello_world():
    return render_template('home.html')


if __name__ == '__main__':
    app.run(host= '0.0.0.0',debug=True)