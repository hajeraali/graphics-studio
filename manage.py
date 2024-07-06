from flask_migrate import MigrateCommand
from flask_script import Manager
from app import app, db  # Make sure to import your app and db from the correct module

manager = Manager(app)
manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()
