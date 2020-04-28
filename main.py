from flask import Flask
from flask.views import MethodView
from flask import request
import os
from dotenv import load_dotenv
load_dotenv
import requests

app = Flask(__name__)
TOKEN = os.environ.get('TOKEN')
TELEGRAM_URL = 'https://api.telegram.org/bot{TOKEN}/sendMessage'


def parse_text(text_msg):
    """/start /help, /job"""

    if '/' in text_msg:
        if '/start' in text_msg or '/help' in text_msg:
            message = '''Для начала работы введите команду /job'''
        return message
    else:
        return None


def send_message(chat_id, tmp):
    pass


@app.route('/', methods=["POST", "GET"])
def index():
    if request.method == "POST":
        resp = request.get_json()
        print(resp)
        return '<h1>Hi BOT / POST!</h1>'
    return '<h1>Hi BOT / GET!</h1>'


class BotAPI(MethodView):

    def get(self):
        return '<h1>Hi BOT from CLASS / GET!</h1>'

    def post(self):
        resp = request.get_json()
        text_msg = resp['message']['text']
        chat_id = resp['message']['chat']['id']
        tmp = parse_text(text_msg)
        if tmp:
            send_message(chat_id, tmp)
        print(resp)
        return '<h1>Hi BOT from CLASS / POST!</h1>'


app.add_url_rule('/TOKEN/', view_func=BotAPI.as_view('bot'))


if __name__ == '__main__':
    app.run()
