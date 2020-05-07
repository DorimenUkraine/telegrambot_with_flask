from app import db, app
from datetime import date, datetime


# As example https://www.youtube.com/watch?v=Y8i_UjuqunQ
class Users(db.Model):
    # Users
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(120), index=True, unique=True)
    last_name = db.Column(db.String(128))
    first_name = db.Column(db.String(128))
    created = db.Column(db.DateTime, default=datetime.now())
    user_days = db.relationship("Days", back_populates="user_days")
    user_tasks = db.relationship("Tasks", back_populates="user_tasks")
    user_chats = db.relationship("Chats", back_populates="user_chats")

    def __init__(self, username, last_name, first_name):
        self.username = username
        self.last_name = last_name
        self.first_name = first_name

    def __repr__(self):
        return '<User {}>'.format(self.username)


# As example https://pythonru.com/uroki/14-sozdanie-baz-dannyh-vo-flask
class Days(db.Model):

    # Days when user has been working
    __tablename__ = 'days'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    owner_id = db.Column(db.Integer(), db.ForeignKey('users.id'))
    day = db.Column(db.Date, default=date.today())
    start = db.Column(db.Boolean, default=True)
    finish = db.Column(db.Boolean, default=False)
    user_days = db.relationship("Users", back_populates="user_days")

    def __init__(self, owner_id):
        self.owner_id = owner_id

    def __repr__(self):
        return '<Days {}>'.format(self.name)


class Tasks(db.Model):

    # User's tasks table
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    owner_id = db.Column(db.Integer(), db.ForeignKey('users.id'))
    day = db.Column(db.DateTime(), db.ForeignKey('days.day'), default=date.today())
    task_id = db.Column(db.String(120), index=True)
    start = db.Column(db.Boolean, default=False)
    finish = db.Column(db.Boolean, default=False)
    created_on = db.Column(db.DateTime, default=datetime.now())
    updated_on = db.Column(db.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow)
    user_tasks = db.relationship("Users", back_populates="user_tasks")

    def __init__(self, owner_id, task_id):
        self.owner_id = owner_id
        self.name = task_id

    def __repr__(self):
        return '<Tasks {}>'.format(self.name)


class Chats(db.Model):

    # User's chat history
    __tablename__ = 'chats'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    owner_id = db.Column(db.Integer(), db.ForeignKey('users.id'))
    chat_id_go = db.Column(db.Integer(), db.ForeignKey('days.day'), default=date.today())
    created_on = db.Column(db.DateTime, default=datetime.now())
    updated_on = db.Column(db.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow)
    user_chats = db.relationship("Users", back_populates="user_chats")

    def __init__(self, owner_id, chat_id):
        self.owner_id = owner_id
        self.chat_id_go = chat_id

    def __repr__(self):
        return '<Chats {}>'.format(self.name)