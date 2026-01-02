import os
from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
from run_ai import get_ai_response
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("CHATBOT_DB")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "your-secret-key-here")

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access the chat.'
login_manager.login_message_category = 'info'


# User model
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    # Relationship: one user has many messages
    messages = db.relationship('Message', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        """Hash and set the user's password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if the provided password matches the hash"""
        return check_password_hash(self.password_hash, password)


# Message model
class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    text = db.Column(db.Text, nullable=True)
    sender = db.Column(db.String(10), nullable=False)  # 'user' or 'bot'
    timestamp = db.Column(db.DateTime, default=datetime.now)


@login_manager.user_loader
def load_user(user_id):
    """Load user from session"""
    return db.session.get(User, int(user_id))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()

        if not user:
            flash('Please fill in all fields.', 'error')
        elif not check_password_hash(user.password_hash, password):
            flash('Password not correct')
            return redirect(url_for('login'))
        else:
            login_user(user)
            flash(f'Welcome back, {username}!', 'success')
            return redirect(url_for('index'))
    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        new_user = User(username=request.form.get('username'), email=request.form.get('email'),
                        password_hash=generate_password_hash(request.form.get('password'), method='pbkdf2:sha256',
                                                             salt_length=8))
        db.session.add(new_user)
        db.session.commit()
        return render_template('index.html', user=new_user)
    return render_template("signup.html")


@app.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    """Chat page - requires authentication"""
    if request.method == 'POST':
        user_message = request.form.get('message', '').strip()

        if user_message:
            # Get last 10 messages for context (adjust number as needed)
            recent_messages = Message.query.filter_by(user_id=current_user.id) \
                .order_by(Message.timestamp.desc()) \
                .limit(20)\
                .all()

            conversation_history = [
                {'text': msg.text, 'sender': msg.sender}
                for msg in reversed(recent_messages)  # Reverse to get chronological order
            ]

            # Save user message
            user_msg = Message(user_id=current_user.id, text=user_message, sender='user')
            db.session.add(user_msg)
            db.session.commit()

            # Get AI response WITH context
            bot_response = get_ai_response(user_message, conversation_history)

            # Save bot response
            bot_msg = Message(user_id=current_user.id, text=bot_response, sender='bot')
            db.session.add(bot_msg)
            db.session.commit()

        return redirect(url_for('index'))

    # Display all messages
    messages = Message.query.filter_by(user_id=current_user.id) \
        .order_by(Message.timestamp.asc()) \
        .all()

    display_messages = [
        {
            'text': msg.text,
            'sender': msg.sender,
            'timestamp': msg.timestamp.strftime('%I:%M %p')
        }
        for msg in messages
    ]

    return render_template('index.html', messages=display_messages, username=current_user.username)


@app.route('/clear', methods=['GET', 'POST'])
@login_required
def clear_messages():
    """Clear all messages for current user"""
    Message.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash('Messages cleared.', 'info')
    return redirect(url_for('index'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
