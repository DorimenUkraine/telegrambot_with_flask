from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from config import Config
from models import Users, Chats, Days, Tasks

app = Flask(__name__)
app.debug = True
app.config.from_object(Config)

db = SQLAlchemy(app)


@app.shell_context_processor
def make_shell_context():
    return dict(db=db, Users=Users, Chats=Chats, Days=Days, Tasks=Tasks)


migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()
