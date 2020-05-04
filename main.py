from flask.views import MethodView
from flask import request
import requests
import json
import os
import logging
from app import db, app
from models import Users
from dotenv import load_dotenv

load_dotenv()

############################### НАСТРОЙКИ ПОДКЛЮЧЕНИЯ К ТЕЛЕГРАМУ ############################################
TOKEN = os.environ.get('TOKEN')
SEND_MESSAGE = 'sendMessage'
EDIT_MESSAGE_REPLY_MARKUP = 'editMessageReplyMarkup'
TELEGRAM_URL = f'https://api.telegram.org/bot{TOKEN}/'


############################### НАСТРОЙКИ РАСПОРЯДКА ДНЯ ПОЛЬЗОВАТЕЛЯ ############################################



############################### ЛОГГИРОВАНИЕ ############################################
# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


############################### ФУНКЦИИ РАБОТЫ С ТЕЛЕГРАМОМ ############################################
def send_message(params):
    """
    Если функция парсинга текста вернула какой-то ответ,
    тогда отправим его на отправку в Телегу обратно простым текстом
    :param params:
    :return:
    """
    session = requests.Session()
    send_url = f'{TELEGRAM_URL}{SEND_MESSAGE}'
    print(send_url)
    r = session.get(send_url, params=params)

    print(r.json())
    return r.json()


def edit_message_reply_markup(params):
    """
        Если функция парсинга команды с кнопки вернула какой-то ответ,
        тогда отредактируем в Телеге сообщение с кнопкой
        :param params:
        :return:
        """
    session = requests.Session()
    edit_message_reply_markup_url = f'{TELEGRAM_URL}{EDIT_MESSAGE_REPLY_MARKUP}'
    print(edit_message_reply_markup_url)
    r = session.get(edit_message_reply_markup_url, params=params)

    print(r.json())
    return r.json()


############################### ФУНКЦИИ ОБРАБОТКИ ДАННЫХ С ТЕЛЕГРАМА ############################################
def parse_text(chat_id, last_name, first_name, username, text_msg):
    """
    Передадим введенный пользователем в Телеге текст на парсинг
    Пока умеем обрабатывать команды /start /help, /job
    """

    if '/' in text_msg:  # Для ориентира, что это команда, найдем в сообщении /

        if text_msg == '/start':
            logger.info(f"Пользователь {username} начал диалог.")

            try:
                find_user_in_db(username, first_name, last_name)
            except NameError:
                print("user не отработал")
            except:
                print("An exception occurred")
            finally:

                message = f'''Привет, *{last_name}* *{first_name}*.'''
                reply_markup = json.dumps(
                    {'inline_keyboard': [[{'text': 'Начнём учёт нашего рабочего дня',
                                           'callback_data': 'go'}]]})
                return dict(chat_id=chat_id,
                            text=message,
                            parse_mode='Markdown',
                            reply_markup=reply_markup)

        elif text_msg == '/help':
            logger.info(f"Пользователь {username} запросил подсказку.")

            message = f'''Пока у нас нет документации'''
            return dict(chat_id=chat_id,
                        text=message,
                        parse_mode='Markdown')

        elif '/go' in text_msg:
            logger.info(f"Пользователь {username} инициировал команду /go.")
            message = f'''Ну что же, *{last_name}* *{first_name}*, приступим!'''
            reply_markup = json.dumps({'inline_keyboard': [[{'text': 'текст3',
                                                             'url': 'http://ya.ru'}]]})
            return dict(chat_id=chat_id,
                        text=message,
                        parse_mode='Markdown',
                        reply_markup=reply_markup)

        else:
            logger.info(f"Пользователь {username} ввел некорректную команду")

            message = f'''*{last_name}* *{first_name}*, Вы ввели некорректную команду!'''
            reply_markup = json.dumps({'inline_keyboard': [[{'text': 'текст4',
                                                             'url': 'http://ya.ru'}]]})
            return dict(chat_id=chat_id,
                        text=message,
                        parse_mode='Markdown',
                        reply_markup=reply_markup)

    else:
        return None


def parse_markup_command(chat_id, last_name, first_name, username, message_id, callback_query):
    """
    Передадим введенный пользователем в Телеге команды на парсинг
    Пока умеем обрабатывать команды: go
    """

    if callback_query == 'go':

        logger.info(f"Пользователь {username} нажал на кнопку go.")
        # message = f'''Добро!'''
        reply_markup = json.dumps({'inline_keyboard': [[{'text': 'текст_go',
                                                         'url': 'http://ya.ru'}]]})
        return dict(chat_id=chat_id,
                    message_id=message_id,
                    # text=message,
                    parse_mode='Markdown',
                    reply_markup=reply_markup)

    else:

        return None


############################### СЛУЖЕБНЫЕ ФУНКЦИИ ############################################
def write_json(data, filename='answer.json'):
    """
    Функция для записи полученных ответов в файл для последующего анализа получемых данных
    :param data:
    :param filename:
    :return:
    """
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)  # indent - разбиение файла на красивый удобочитаемый вид (
        # каждая строчка - 2 пробела); ensure_ascii=False - если
        #  проблема с unicode error из-за текстов на русском языке


def add_users_to_db(username, last_name, first_name):
    """
    Функция добавления пользователя в БД
    :return:
    """
    data = Users(username, last_name, first_name)
    db.session.add(data)
    db.session.commit()


def find_user_in_db(username, first_name, last_name):
    """
    Функция для проверки наличия пользователя в базе и при отсутствии оного добавление
    :param username:
    :param first_name:
    :param last_name:
    :return:
    """
    user = db.session.query(Users).filter(Users.username == f'{username}').first_or_404()
    print(user)
    if not user:
        add_users_to_db(username, first_name, last_name)



############################### FLASK ############################################
@app.route('/', methods=["POST", "GET"])
def index():
    """
    Можно получать post и get через встроенную функцию
    :return:
    """
    if request.method == "POST":
        return '<h1>Hi. It\'s TELEGRAM BOT / POST!</h1>'
    return '<h1>Hi. It\'s TELEGRAM BOT / GET!</h1>'


class BotAPI(MethodView):
    """
    А можно с помощью готовой вьюхи из Flask для обработки get и post запросов.
    Воспользуюсь этим вариантом
    """

    def get(self):
        return '<h1>TELEGRAM BOT welcomes you! / GET!</h1>'

    def post(self):
        # Преобразуем строку из браузера в json и вытащим нужные нам данные
        resp = request.get_json()
        # запишем их в файл для анализа
        write_json(resp)
        # вытаскиваем из json нужные нам данные
        for key in resp:

            if 'message' in key:
                text_msg = resp['message']['text']
                chat_id = resp['message']['chat']['id']
                first_name = resp['message']['chat']['first_name']
                last_name = resp['message']['chat']['last_name']
                username = resp['message']['chat']['username']

                # Передадим введенный пользователем в Телеге текст на парсинг и получим оттуда данные для отправки
                params = parse_text(chat_id, last_name, first_name, username, text_msg)
                print(params)

                # Если функция парсинга текста вернула какой-то ответ, тогда отправим его на отправку в Телегу обратно
                if params:
                    send_message(params)

                break

            elif 'callback_query' in key:
                callback_query = resp['callback_query']['data']
                chat_id = resp['callback_query']['message']['chat']['id']
                message_id = resp['callback_query']['message']['message_id']
                first_name = resp['callback_query']['message']['chat']['first_name']
                last_name = resp['callback_query']['message']['chat']['last_name']
                username = resp['callback_query']['message']['chat']['username']

                # Передадим введенный пользователем в Телеге текст на парсинг и получим оттуда данные для отправки
                params = parse_markup_command(chat_id, last_name, first_name, username, message_id, callback_query)

                # Если функция парсинга текста вернула какой-то ответ, тогда отправим его на отправку в Телегу обратно
                if params:
                    edit_message_reply_markup(params)

                break

        return '<h1>TELEGRAM BOT welcomes you! / POST!</h1>'


# Типовый Flask-обработчик урла, вызывающий класс
app.add_url_rule('/TOKEN/', view_func=BotAPI.as_view('bot'))

# Запустим код
if __name__ == '__main__':
    app.run()
