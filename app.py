from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'jarvis_secret_key_123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User Table
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Routes ---

@app.route('/')
@login_required
def home():
    return render_template('index.html', name=current_user.username)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('home'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        
        new_user = User.query.filter_by(username=username).first()
        if new_user:
            flash('Username already exists!')
            return redirect(url_for('register'))
            
        new_user = User(username=username, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

# --- J.A.R.V.I.S. Brain (No changes to logic) ---
conversation_history = []
API_KEY = os.environ.get("GROQ_API_KEY")

@app.route('/ask', methods=['POST'])
@login_required
def ask():
    global conversation_history
    data = request.json
    user_query = data.get('query')
    conversation_history.append({"role": "user", "content": user_query})
    if len(conversation_history) > 10: conversation_history = conversation_history[-10:]

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "system", "content": "You are J.A.R.V.I.S. Respond to " + current_user.username + " as 'Sir'."}] + conversation_history
    }
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=20)
        bot_reply = res.json()['choices'][0]['message']['content']
        conversation_history.append({"role": "assistant", "content": bot_reply})
        return jsonify({'reply': bot_reply})
    except:
        return jsonify({'reply': "Error connecting, Sir."})

if __name__ == "__main__":
    with app.app_context():
        db.create_all() # Database create karega
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
        
