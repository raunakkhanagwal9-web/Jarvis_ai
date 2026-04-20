from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import os

# --- Flask App Setup ---
app = Flask(__name__)

# Security & Database Configuration
app.config['SECRET_KEY'] = 'jarvis_secret_key_999'
# Database file ka path fix kiya hai taaki Render ise dhund sake
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Database aur Login Manager initialize karein
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- Database Model ---
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
    # current_user.username se Jarvis ko pata chalega ki aap Raunak Sir ho
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
        else:
            flash('Invalid username or password, Sir.')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Check agar user pehle se hai
        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash('This username is already taken, Sir.')
            return redirect(url_for('register'))
            
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- J.A.R.V.I.S. Brain Logic ---
conversation_history = []
API_KEY = os.environ.get("GROQ_API_KEY")

@app.route('/ask', methods=['POST'])
@login_required
def ask():
    global conversation_history
    data = request.json
    user_query = data.get('query')
    
    if not API_KEY:
        return jsonify({'reply': "Sir, API Key missing hai Render settings mein."})

    # Memory Management
    conversation_history.append({"role": "user", "content": user_query})
    if len(conversation_history) > 10:
        conversation_history = conversation_history[-10:]

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Adaptive Tone & Personalized Greeting
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {
                "role": "system", 
                "content": f"You are J.A.R.V.I.S., a witty and intelligent assistant. Address the user as '{current_user.username} Sir'. Never use the word 'Boss'. Use Hinglish, be cool like Iron Man's assistant, and use Markdown for structured answers."
            }
        ] + conversation_history
    }
    
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=20)
        bot_reply = res.json()['choices'][0]['message']['content'].strip()
        conversation_history.append({"role": "assistant", "content": bot_reply})
        return jsonify({'reply': bot_reply})
    except Exception as e:
        return jsonify({'reply': "Connection busy hai, Sir!"})

# --- App Execution ---
if __name__ == "__main__":
    # Tables create karna zaroori hai pehli baar ke liye
    with app.app_context():
        db.create_all()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
