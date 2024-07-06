from flask import Flask, request, render_template, send_from_directory, jsonify, redirect, url_for, flash, session
import os
from main import process_image
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from sqlalchemy import text
from flask_migrate import Migrate


app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:123@localhost/graphics_studio'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'

# Initialize SQLAlchemy, Bcrypt, Migrate, and Mail
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
migrate = Migrate(app, db)


# Models
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

  

    
class Admin(db.Model):
    __tablename__ = 'admin'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    login_count = db.Column(db.Integer, nullable=False)
    total_operations = db.Column(db.Integer, nullable=False, default=0)

    user = db.relationship('User', backref='logins')

    def __init__(self, user_id, login_count, total_operations=0):
        self.user_id = user_id
        self.login_count = login_count
        self.total_operations = total_operations

# Ensure folders exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(PROCESSED_FOLDER):
    os.makedirs(PROCESSED_FOLDER)

# Routes
@app.route('/')
def index():
    if 'logged_in' in session and session['logged_in']:
        return render_template('index.html', logged_in=True)
    else:
        return render_template('index.html', logged_in=False)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'image' not in request.files:
        return 'No file part'
    file = request.files['image']
    if file.filename == '':
        return 'No selected file'
    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        return send_from_directory(app.config['UPLOAD_FOLDER'], file.filename)

@app.route('/process', methods=['POST'])
def process_file():
    if 'logged_in' in session and session['logged_in']:
        data = request.json
        filename = data['filename']
        operation = data['operation']
        value = data['value']
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        if not os.path.exists(filepath):
            filepath = os.path.join(app.config['PROCESSED_FOLDER'], filename)

        output_filename = process_image(filepath, operation, value, app.config['PROCESSED_FOLDER'])

        # Update total_operations for the logged-in admin
        user = User.query.filter_by(username=session['username']).first()
        admin_entry = Admin.query.filter_by(user_id=user.id).first()
        if admin_entry:
            admin_entry.total_operations += 1
            db.session.commit()

        return jsonify({'processedImagePath': f"/processed/{output_filename}", 'newProcessedFilename': output_filename})
    else:
        return jsonify({'error': 'User not logged in'}), 403

@app.route('/processed/<filename>')
def get_processed_file(filename):
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')

    if User.query.filter_by(username=username).first():
        flash('Username already exists.', 'error')
        return redirect(url_for('index'))
    if User.query.filter_by(email=email).first():
        flash('Email already exists.', 'error')
        return redirect(url_for('index'))

    new_user = User(username=username, email=email, password=password)
    db.session.add(new_user)
    db.session.commit()

    flash('Registration successful. Please log in.', 'success')
    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    user = User.query.filter_by(username=username).first()
    if user and bcrypt.check_password_hash(user.password_hash, password):
        session['logged_in'] = True
        session['username'] = username
        user.increment_login_count()
        admin_entry = Admin.query.filter_by(user_id=user.id).first()
        if not admin_entry:
            admin_entry = Admin(user_id=user.id, login_count=user.login_count, total_operations=0)
            db.session.add(admin_entry)
        admin_entry.login_count = user.login_count
        db.session.commit()

        flash('You have successfully logged in.', 'success')
        return redirect(url_for('index'))
    else:
        flash('Invalid username or password.', 'error')
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    flash('You have successfully logged out.', 'success')
    return redirect(url_for('index'))

@app.route('/update-password', methods=['POST'])
def update_password():
    email = request.form.get('email')
    new_password = request.form.get('password')

    user = User.query.filter_by(email=email).first()
    if user:
        user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
        db.session.commit()
        flash('Password updated successfully.', 'success')
    else:
        flash('User not found.', 'error')

    return redirect(url_for('index'))

@app.route('/delete-account/<int:user_id>', methods=['POST'])
def delete_account(user_id):
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash('Account deleted successfully.')
    else:
        flash('User not found.')

    return redirect(url_for('index'))


@app.route('/test-db')
def test_db_connection():
    try:
        result = db.session.execute(text('SELECT 1'))
        if result.scalar() == 1:
            return 'Database connection successful!'
        else:
            return 'Database connection failed.'
    except Exception as e:
        return f'Database connection failed: {str(e)}'

if __name__ == '__main__':
    app.run(debug=True)
