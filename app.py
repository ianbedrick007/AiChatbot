import os
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
from run_ai import get_ai_response
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.getenv("CHATBOT_DB")
)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Messages(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, unique=True, nullable=False)
    user_message = db.Column(db.Text, nullable=False)
    bot_response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now())


@app.route('/', methods=['GET', 'POST'])
def index():
    """Handle both displaying messages and processing new messages"""
    if request.method == 'POST':
        user_message = request.form.get('message', '').strip()

        if user_message:
            bot_response = get_ai_response(user_message)

            # Fetch or create the user's message row
            convo = Messages.query.filter_by(user_id=1).first()

            if convo:
                convo.user_message += f"\n{user_message}"
                convo.bot_response += f"\n{bot_response}"
                convo.timestamp = datetime.now()
            else:
                convo = Messages(
                    user_id=1,
                    user_message=user_message,
                    bot_response=bot_response
                )
                db.session.add(convo)

            db.session.commit()

        return redirect(url_for('index'))

    convo = Messages.query.filter_by(user_id=1).first()
    display_messages = []

    if convo:
        user_lines = convo.user_message.strip().split('\n')
        bot_lines = convo.bot_response.strip().split('\n')

        for user, bot in zip(user_lines, bot_lines):
            display_messages.append({'text': user, 'sender': 'user'})
            display_messages.append({'text': bot, 'sender': 'bot'})

    return render_template('index.html', messages=display_messages)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
