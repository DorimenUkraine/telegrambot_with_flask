from datetime import datetime
from app import db


# Сделал по видео https://www.youtube.com/watch?v=Y8i_UjuqunQ
class Users(db.Model):
    # Создаем таблицу пользователей
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), index=True, unique=True)
    last_name = db.Column(db.String(128))
    first_name = db.Column(db.String(128))
    created = db.Column(db.DateTime, default=datetime.now())

    # Загоним данные в БД транзитом
    # def __init__(self, *args, **kwargs):
    #     super(Users, self).__init__(*args, **kwargs)

    def __init__(self, username, last_name, first_name):
        self.username = username
        self.last_name = last_name
        self.first_name = first_name

    def __repr__(self):
        return '<User {}>'.format(self.username)
