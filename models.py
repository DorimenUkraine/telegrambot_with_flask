from datetime import datetime
from app import db


# Сделал по видео https://www.youtube.com/watch?v=Y8i_UjuqunQ
class Users(db.Model):
    # Создаем таблицу пользователей
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), index=True, unique=True)
    last_name = db.Column(db.String(128))
    first_name = db.Column(db.String(128))
    created = db.Column(db.DateTime, default=datetime.now())
    tasks = db.relationship('Tasks', backref='tasks')

    def __init__(self, username, last_name, first_name):
        self.username = username
        self.last_name = last_name
        self.first_name = first_name

    def __repr__(self):
        return '<User {}>'.format(self.username)


# Взял за основу https://pythonru.com/uroki/14-sozdanie-baz-dannyh-vo-flask
class Tasks(db.Model):
    # Создаем таблицу задач пользователей
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer(), db.ForeignKey('users.id'))
    name = db.Column(db.String(120), index=True)
    start = db.Column(db.Boolean, default=False)
    finish = db.Column(db.Boolean, default=False)
    created_on = db.Column(db.DateTime, default=datetime.now())
    updated_on = db.Column(db.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, name, owner_id):
        self.owner_id = owner_id
        self.name = name

    def __repr__(self):
        return '<Tasks {}>'.format(self.name)
