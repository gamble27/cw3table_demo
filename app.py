from flask import Flask, request
from flask_sslify import SSLify
from static.bot import AppManager
import json

app = Flask(__name__)
sslify = SSLify(app)

bot = AppManager()


@app.route('/', methods=["POST", "GET"])
def index():
    if request.method == "POST":
        response = request.get_json()  # ensure_ascii = true??
        bot.handle_msg(response)
    return 'Hello World!'


if __name__ == '__main__':
    app.run()
