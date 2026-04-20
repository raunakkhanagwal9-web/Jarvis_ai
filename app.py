from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import os

# --- Flask App Setup ---
app = Flask(__name__)

# Security & Database Configuration
app.config['SECRET_KEY'] = 'jarvis_stark_industries_key'
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

# --- Authentication Routes ---

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
            flash('Identification failed. Invalid credentials, Sir.')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash('This identity already exists in our database, Sir.')
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

# --- Main App Route ---

@app.route('/')
@login_required
def home():
    # 'name' variable index.html ko pass kiya ja raha hai
    return render_template('index.html', name=current_user.username)

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
        return jsonify({'reply': "Sir, Groq API Key is missing in Render environment settings."})

    # Memory (Context)
    conversation_history.append({"role": "user", "content": user_query})
    if len(conversation_history) > 10:
        conversation_history = conversation_history[-10:]

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 🔥 PERSONALIZED SYSTEM PROMPT 🔥
    # Jarvis ko user ka asli naam pata chal jayega
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {
                "role": "system", 
                "content": f"You are J.A.R.V.I.S., the advanced AI assistant. Your user is {current_user.username}. Address them as '{current_user.username} Sir'. Never use the word 'Boss'. Speak in witty Hinglish, be intelligent, and use Markdown for all technical or structured information."
            }
        ] + conversation_history
    }
    
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=20)
        bot_reply = res.json()['choices'][0]['message']['content'].strip()
        conversation_history.append({"role": "assistant", "content": bot_reply})
        return jsonify({'reply': bot_reply})
    except Exception:
        return jsonify({'reply': "Protocol error, Sir. I'm having trouble connecting."})

# --- Initialize Database ---
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
