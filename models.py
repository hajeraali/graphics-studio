from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import random
import string

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    reset_token = db.Column(db.String(100), nullable=True)  # New field for reset token
    login_count = db.Column(db.Integer, default=0)

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    @staticmethod
    def find_by_username(username):
        return User.query.filter_by(username=username).first()

    @staticmethod
    def find_by_email(email):
        return User.query.filter_by(email=email).first()

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def increment_login_count(self):
        self.login_count += 1
        db.session.commit()

    def generate_reset_token(self):
        token = ''.join(random.choices(string.ascii_letters + string.digits, k=50))
        self.reset_token = token
        db.session.commit()
        return token

    def clear_reset_token(self):
        self.reset_token = None
        db.session.commit()


   
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