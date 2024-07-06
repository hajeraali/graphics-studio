 from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask import Flask

db = SQLAlchemy()
bcrypt = Bcrypt()

from sqlalchemy import Column, Integer
from sqlalchemy.orm import relationship

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    login_count = db.Column(db.Integer, default=0)

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    # Other methods (find_by_username, find_by_email, check_password) remain the same

    def increment_login_count(self):
        self.login_count += 1
        db.session.commit()


    @staticmethod
    def find_by_username(username):
        return User.query.filter_by(username=username).first()

    @staticmethod
    def find_by_email(email):
        return User.query.filter_by(email=email).first()

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)
  

   
class Admin(db.Model):
    __tablename__ = 'admin'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    login_count = db.Column(db.Integer, nullable=False)
    total_operations = db.Column(db.Integer, nullable=False, default=0)  # New column

    user = relationship('User', backref='logins')

    def __init__(self, user_id, login_count, total_operations=0):
        self.user_id = user_id
        self.login_count = login_count
        self.total_operations = total_operations