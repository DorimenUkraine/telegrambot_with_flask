import json
import logging
import os
import time
import requests
from dotenv import load_dotenv
from datetime import datetime, date, timedelta
from flask import request
from flask.views import MethodView
from multiprocessing import Process
import random, string


# Работа с отладчиком: https://habr.com/ru/post/104086/
# https://tproger.ru/translations/debugging-python-with-pdb/
# https://youtu.be/N0xkFZv2Df0?t=582
import pdb

pdb.set_trace()

from app import db, app
from models import Users, Days, Chats, Tasks

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
    Пока умеем обрабатывать команды /start /help
    """
    # Find user in DB. If it's not in DB - add. If it's already in DB - update data if change
    try:
        find_user_in_db(username, first_name, last_name)
    except NameError:
        logger.info("Локальное или глобальное имя не найдено")
    except ImportError:
        logger.info("Оператор import не может найти определение модуля!")
    except ValueError:
        logger.info(
            "Встроенная операция или функция получает аргумент, тип которого правильный, но неправильно значение")
    except:
        logger.info("Не корректно работает работа с БД")

    finally:

        if '/' in text_msg:  # Для ориентира, что это команда, найдем в сообщении /

            if text_msg == '/start':
                logger.info(f"Пользователь {username} написал в чат /start.")

                user_from_db = db.session.query(Users).filter(Users.username == f'{username}').first()
                owner_id = user_from_db.id

                chat_from_db = db.session.query(Chats).filter(Chats.chat_id_go == f'{chat_id}').first()

                if not chat_from_db or chat_from_db is None:
                    add_chat_id_to_db(owner_id, chat_id)

                message = f'''Привет, *{last_name}* *{first_name}*.'''
                reply_markup = json.dumps(
                    {'keyboard': [[{'text': 'Начнём учёт рабочего дня',
                                    'callback_data': 'go'}]],
                     'resize_keyboard': True,
                     'one_time_keyboard': True})

                return dict(chat_id=chat_id,
                            text=message,
                            parse_mode='Markdown',
                            reply_markup=reply_markup)

            elif text_msg == '/help':
                logger.info(f"Пользователь {username} написал в чат /help.")

                message = f'''Пока у нас нет документации'''
                return dict(chat_id=chat_id,
                            text=message,
                            parse_mode='Markdown')

            else:
                logger.info(f"Пользователь {username} ввел некорректную команду")

                message = f'''*{last_name}* *{first_name}*, Вы ввели некорректную команду!'''

                return dict(chat_id=chat_id,
                            text=message,
                            parse_mode='Markdown')

        elif 'Начнём' in text_msg:
            logger.info(f"Пользователь {username} написал в чате Начнём")

            # Если написал "Начнём", тогда начнем его рабочий день
            user_from_db = db.session.query(Users).filter(Users.username == f'{username}').first()
            owner_id = user_from_db.id
            day_from_db = db.session.query(Days).filter(Days.owner_id == owner_id, Days.day == date.today()).first()

            if not day_from_db or day_from_db is None:
                add_day_to_db(owner_id)

                day_from_db = db.session.query(Days).filter(Days.owner_id == owner_id, Days.day == date.today()).first()
                day = day_from_db.day

                # Запускаем в параллельном потоке работу с задачами пользователя и при этом программе позволяем
                # реагировать на другие команды
                process_generator(last_name, first_name, owner_id, chat_id, day)

                message = f'''Добро!'''

                return dict(chat_id=chat_id,
                            text=message,
                            parse_mode='Markdown')

            else:
                user_from_db = db.session.query(Users).filter(Users.username == f'{username}').first()
                owner_id = user_from_db.id
                chat_from_db = db.session.query(Chats).filter(Chats.owner_id == f'{owner_id}').first()
                chat_id = chat_from_db.chat_id_go
                print(chat_id)

                day = day_from_db.day

                # Запускаем в параллельном потоке работу с задачами пользователя и при этом программе позволяем
                # реагировать на другие команды
                process_generator(last_name, first_name, owner_id, chat_id, day)

                message = f'''*{last_name}* *{first_name}*, Вы уже запустили сегодня рабочий день'''

                return dict(chat_id=chat_id,
                            text=message,
                            parse_mode='Markdown')

        elif 'Работаю' in text_msg:
            logger.info(f"Пользователь {username} написал в чате Работаю.")
            message = f'''Добро!'''

            # Если написал "Работаю", тогда начнем его рабочий день
            user_from_db = db.session.query(Users).filter(Users.username == f'{username}').first()

            owner_id = user_from_db.id
            day_from_db = db.session.query(Days).filter(Days.owner_id == owner_id, Days.day == date.today()).first()

            if not day_from_db or day_from_db is None or day_from_db.start == False:
                add_day_to_db(owner_id)

                day_from_db = db.session.query(Days).filter(Days.owner_id == owner_id, Days.day == date.today()).first()
                day = day_from_db.day

                # Запускаем в параллельном потоке работу с задачами пользователя и при этом программе позволяем
                # реагировать на другие команды
                process_generator(last_name, first_name, owner_id, chat_id, day)

                return dict(chat_id=chat_id,
                            text=message,
                            parse_mode='Markdown')

            else:
                user_from_db = db.session.query(Users).filter(Users.username == f'{username}').first()
                owner_id = user_from_db.id
                chat_from_db = db.session.query(Chats).filter(Chats.owner_id == f'{owner_id}').first()
                chat_id = chat_from_db.chat_id_go
                print(chat_id)
                message = f'''*{last_name}* *{first_name}*, Вы уже запустили сегодня рабочий день'''

                day_from_db = db.session.query(Days).filter(Days.owner_id == owner_id, Days.day == date.today()).first()
                day = day_from_db.day

                # Запускаем в параллельном потоке работу с задачами пользователя и при этом программе позволяем
                # реагировать на другие команды
                process_generator(last_name, first_name, owner_id, chat_id, day)

                return dict(chat_id=chat_id,
                            text=message,
                            parse_mode='Markdown')

        else:
            return None


def parse_markup_command(chat_id, last_name, first_name, username, message_id, callback_query):
    """
    Передадим введенные пользователем в Телеге команды на парсинг
    Пока умеем обрабатывать команды: go
    """

    # Find user in DB. If it's not in DB - add. If it's already in DB - update data if change
    try:
        find_user_in_db(username, first_name, last_name)
    except NameError:
        logger.info("Локальное или глобальное имя не найдено")
    except ImportError:
        logger.info("Оператор import не может найти определение модуля!")
    except ValueError:
        logger.info(
            "Встроенная операция или функция получает аргумент, тип которого правильный, но неправильно значение")
    except:
        logger.info("Не корректно работает работа с БД")

    finally:

        if callback_query == 'go':

            logger.info(f"Пользователь {username} нажал на кнопку go.")
            message = f'''Добро!'''

            # Если нажал на go, тогда начнем его рабочий день
            user_from_db = db.session.query(Users).filter(Users.username == f'{username}').first()

            owner_id = user_from_db.id
            day_from_db = db.session.query(Days).filter(Days.owner_id == owner_id, Days.day == date.today()).first()

            if not day_from_db or day_from_db is None or day_from_db.start == False:
                add_day_to_db(owner_id)

                day_from_db = db.session.query(Days).filter(Days.owner_id == owner_id, Days.day == date.today()).first()
                day = day_from_db.day

                # Запускаем в параллельном потоке работу с задачами пользователя и при этом программе позволяем
                # реагировать на другие команды
                process_generator(last_name, first_name, owner_id, chat_id, day)

                return dict(chat_id=chat_id,
                            message_id=message_id,
                            text=message,
                            parse_mode='Markdown')

            else:
                user_from_db = db.session.query(Users).filter(Users.username == f'{username}').first()
                owner_id = user_from_db.id
                chat_from_db = db.session.query(Chats).filter(Chats.owner_id == f'{owner_id}').first()
                chat_id = chat_from_db.chat_id_go
                print(chat_id)
                message = f'''*{last_name}* *{first_name}*, Вы уже запустили сегодня рабочий день'''

                reply_markup = json.dumps({'remove_keyboard': True})

                day_from_db = db.session.query(Days).filter(Days.owner_id == owner_id, Days.day == date.today()).first()
                day = day_from_db.day

                # Запускаем в параллельном потоке работу с задачами пользователя и при этом программе позволяем
                # реагировать на другие команды
                process_generator(last_name, first_name, owner_id, chat_id, day)

            return dict(chat_id=chat_id,
                        text=message,
                        parse_mode='Markdown',
                        reply_markup=reply_markup)


        else:

            return None


############################### ФУНКЦИИ РАБОТЫ С ЗАДАЧАМИ ПОЛЬЗОВАТЕЛЯ ############################################
def calculate_interval(hour, key, last_name, first_name, owner_id, chat_id, day, name_of_work):
    # Convert all times in seconds for calculate
    start_interval_in_seconds = hour * 60 * 60
    now_in_seconds = (datetime.now().minute * 60) + (datetime.now().hour * 60 * 60) + datetime.now().second
    time_for_working_in_seconds = int(timedelta(minutes=45).total_seconds())
    how_much_work = now_in_seconds - start_interval_in_seconds
    print('''Calculate is working''')
    if now_in_seconds > start_interval_in_seconds and (now_in_seconds - start_interval_in_seconds) < (
            time_for_working_in_seconds):

        task_from_db = db.session.query(Tasks).filter(Tasks.owner_id == f'{owner_id}', Tasks.day == f'{day}',
                                                      Tasks.task_id == f'{key}').first()
        print(task_from_db)
        if not task_from_db or task_from_db is None or task_from_db.task_id != f'{key}':

            add_task_to_db(owner_id, key)

            work_or_not(how_much_work, last_name, first_name, chat_id, name_of_work, key, day, owner_id)

        else:

            work_or_not(how_much_work, last_name, first_name, chat_id, name_of_work, key, day, owner_id)

    elif time_for_working_in_seconds == (now_in_seconds - start_interval_in_seconds) < (
            time_for_working_in_seconds + 20):

        print('''Time to relax''')
        time_for_relax(last_name, first_name, chat_id)


def work_or_not(how_much_work, last_name, first_name, chat_id, name_of_work, key, day, owner_id):
    if how_much_work <= 300:

        work_or_not_from_db = db.session.query(Tasks).filter(Tasks.owner_id == f'{owner_id}', Tasks.day == f'{day}',
                                                             Tasks.task_id == f'{key}').first()
        print(work_or_not_from_db)
        if not work_or_not_from_db.work_or_not:
            print(work_or_not_from_db.work_or_not)
            update_task_work_or_not_to_db(owner_id, key, day)

            message = f'''*{last_name}* *{first_name}*, Вы уже {str(timedelta(seconds=how_much_work))} должны работать над задачей: {name_of_work}. Нажмите на кнопку ниже, чтобы зафиксировать Вашу работу. Осталось {how_much_work - 300} секунд, чтобы успеть зафиксировать факт работы.'''

            reply_markup = json.dumps(
                {'keyboard': [[{'text': 'Работаю. Все ок.',
                                'callback_data': 'user_is_working'}]],
                 'resize_keyboard': True,
                 'one_time_keyboard': True})

            params = dict(chat_id=chat_id,
                          text=message,
                          parse_mode='Markdown',
                          reply_markup=reply_markup)

            send_message(params)

    else:

        work_or_not_from_db = db.session.query(Tasks).filter(Tasks.owner_id == f'{owner_id}', Tasks.day == f'{day}',
                                                             Tasks.task_id == f'{key}').first()
        print(work_or_not_from_db)
        if not work_or_not_from_db.work_or_not:
            print(work_or_not_from_db.work_or_not)
            update_task_work_or_not_to_db(owner_id, key, day)

            message = f'''*{last_name}* *{first_name}*, Вы уже {str(timedelta(seconds=how_much_work))} должны работать над задачей: {name_of_work}. Вы не успели зафиксировать работы и теперь она не будет засчитана'''

            params = dict(chat_id=chat_id,
                          text=message,
                          parse_mode='Markdown')

            send_message(params)


def time_for_relax(last_name, first_name, chat_id):
    message = f'''*{last_name}* *{first_name}*, пора сделать перерыв. Нажмите на кнопку ниже, чтобы зафиксировать факт завершения работы.'''

    reply_markup = json.dumps(
        {'keyboard': [[{'text': 'Отдыхаю',
                        'callback_data': 'user_is_relaxing'}]],
         'resize_keyboard': True,
         'one_time_keyboard': True})

    params = dict(chat_id=chat_id,
                  text=message,
                  parse_mode='Markdown',
                  reply_markup=reply_markup)

    send_message(params)


def working_time(name_of_process, last_name, first_name, owner_id, chat_id, day, delay=15):
    print('Process %s starting...' % name_of_process)

    now_is = datetime.now()

    # Start and finish day parameters
    start_day = now_is.replace(hour=9, minute=0)
    finish_day = now_is.replace(hour=20, minute=0)

    # List of Schedule
    schedule_working_list = {key: value for key, value in enumerate([hour for hour in range(9, 19)])}

    # Table of Schedule
    schedule_working_hours = {'0': 'Первая',
                              '1': 'Вторая',
                              '2': 'Третья',
                              '3': 'Четвертая',
                              '4': 'Пятая',
                              '5': 'Шестая',
                              '6': 'Седьмая',
                              '7': 'Восьмая',
                              '8': 'Девятая',
                              '9': 'Десятая'}

    while start_day.hour <= now_is.hour <= finish_day.hour:
        time.sleep(delay)

        for key, hour in schedule_working_list.items():

            if now_is.hour == hour:
                calculate_interval(hour, key, last_name, first_name, owner_id, chat_id, day,
                                   schedule_working_hours.get(f'{key}'))

    print('Process %s exiting...' % name_of_process)


############################### СЛУЖЕБНЫЕ ФУНКЦИИ ############################################
def process_generator(last_name, first_name, owner_id, chat_id, day):
    tmp = random.random()
    print(tmp)
    pn = Process(target=working_time,
                 args=(f'просчет работы пользователя {tmp}', last_name, first_name, owner_id, chat_id, day))
    pn.start()


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
    u = Users(username, last_name, first_name)
    db.session.add(u)
    db.session.commit()


def update_users_to_db(update_username, username, last_name, first_name):
    """
    Функция добавления пользователя в БД
    :return:
    """

    # Добавить в будущем
    pass


def add_day_to_db(owner_id):
    """
    Функция добавления пользователя в БД
    :return:
    """
    d = Days(owner_id)
    db.session.add(d)
    db.session.commit()


def add_chat_id_to_db(owner_id, chat_id):
    """
    Функция добавления id чата в БД
    :return:
    """
    c = Chats(owner_id, chat_id)
    db.session.add(c)
    db.session.commit()


def update_chat_id_to_db(owner_id, chat_id):
    """
    Функция обновления id чата в БД
    :return:
    """
    c = Chats.query.filter_by(owner_id=f'{owner_id}').update(dict(chat_id_go=f'{chat_id}'))
    db.session.add(c)
    db.session.commit()


def add_task_to_db(owner_id, task_id):
    """
    Функция добавления id чата в БД
    :return:
    """
    t = Tasks(owner_id, task_id)
    db.session.add(t)
    db.session.commit()


def update_task_work_or_not_to_db(owner_id, key, day):
    """
    Функция обновления учета времени задачи в БД
    :return:
    """
    t = db.session.query(Tasks).filter(Tasks.owner_id == f'{owner_id}', Tasks.task_id == f'{key}',
                                       Tasks.day == f'{day}').first().update({'work_or_not': True})
    db.session.add(t)
    db.session.commit()


def find_user_in_db(username, first_name, last_name):
    """
    Функция для проверки наличия пользователя в базе и при отсутствии оного добавление
    А также обновление данных, если они изменились в Телеграме
    :param username:
    :param first_name:
    :param last_name:
    :return:
    """

    user_from_db = db.session.query(Users).filter(Users.username == f'{username}').first()
    print(user_from_db)
    if not user_from_db or user_from_db is None:
        add_users_to_db(username, first_name, last_name)
    else:
        # Тут еще можно в будущем сделать, чтобы проверять изменение данных пользователя
        # и обновлять в БД. Пока без этого.
        pass


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

            # Проверим - это текст или команда через парсинг входящего массива и поиска подходящих конструкций
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
                    send_message(params)

                break

        return '<h1>TELEGRAM BOT welcomes you! / POST!</h1>'


# Типовый Flask-обработчик урла, вызывающий класс
app.add_url_rule('/TOKEN/', view_func=BotAPI.as_view('bot'))

# Запустим код
if __name__ == '__main__':
    app.run()
