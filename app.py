from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
import requests
import os
from authlib.integrations.flask_client import OAuth

app = Flask(__name__)
# Render/Proxy support ke liye
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.config['SECRET_KEY'] = 'jarvis_secret_protocol_777'

# --- ☁️ MONGODB CLOUD SETUP ---
# Aapka permanent connection link
app.config["MONGO_URI"] = "mongodb+srv://raunakkhanagwal9_db_user:52Cqed7w1hCkE4xt@cluster0.czmwhtn.mongodb.net/jarvis_db?retryWrites=true&w=majority&appName=Cluster0"
mongo = PyMongo(app)
db = mongo.db.users      # Users table
chat_db = mongo.db.chats # History table

# --- 🔐 LOGIN MANAGER ---
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.email = user_data['email']
        self.username = user_data['username']

@login_manager.user_loader
def load_user(user_id):
    try:
        user_data = db.find_one({"_id": ObjectId(user_id)})
        return User(user_data) if user_data else None
    except:
        return None

# --- 🌐 GOOGLE OAUTH SETUP ---
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id='869230187120-5531gadmiu9arhb2nsi9p5dkdqqj7elf.apps.googleusercontent.com',
    client_secret='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',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# --- 🛣️ ROUTES ---

@app.route('/')
@login_required
def home():
    return render_template('index.html', name=current_user.username)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email').strip()
        password = request.form.get('password').strip()
        user_data = db.find_one({"email": email})
        
        if not user_data:
            flash('User not found, Sir.')
        elif not check_password_hash(user_data['password'], password):
            flash('Invalid passcode, Sir.')
        else:
            login_user(User(user_data))
            return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/login/google')
def google_login():
    redirect_uri = url_for('google_authorize', _external=True, _scheme='https')
    return google.authorize_redirect(redirect_uri)

@app.route('/login/google/authorize')
def google_authorize():
    token = google.authorize_access_token()
    user_info = token.get('userinfo')
    if not user_info:
        user_info = google.get('https://openidconnect.googleapis.com/v1/userinfo').json()
    
    email = user_info.get('email')
    name = user_info.get('name', 'Jarvis User')

    user_data = db.find_one({"email": email})
    if not user_data:
        new_user = {
            "email": email,
            "username": name,
            "password": generate_password_hash("google_bypass", method='pbkdf2:sha256')
        }
        user_id = db.insert_one(new_user).inserted_id
        user_data = db.find_one({"_id": user_id})
    
    login_user(User(user_data))
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email').strip()
        username = request.form.get('username').strip()
        password = request.form.get('password').strip()
        
        if db.find_one({"email": email}):
            flash('Email already registered, Sir.')
            return redirect(url_for('register'))
            
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        db.insert_one({"email": email, "username": username, "password": hashed_pw})
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    return render_template('register.html')

# --- 🧠 AI LOGIC WITH MEMORY ---

@app.route('/ask', methods=['POST'])
@login_required
def ask():
    data = request.json
    query = data.get('query')
    
    # 1. User ki query save karo database mein
    chat_db.insert_one({
        "user_id": current_user.id,
        "query": query,
        "role": "user"
    })

    # 2. Purani history nikalna context ke liye (Last 5 chats)
    past_chats = list(chat_db.find({"user_id": current_user.id}).sort("_id", -1).limit(6))
    
    messages = [{"role": "system", "content": f"You are J.A.R.V.I.S., a highly advanced AI. User is {current_user.username} Sir. Be polite and efficient."}]
    
    # History ko sahi order mein lagana
    for chat in reversed(past_chats):
        messages.append({"role": "user", "content": chat['query']})

    API_KEY = os.environ.get("GROQ_API_KEY")
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.7
    }
    
    try:
        res = requests.post(url, headers=headers, json=payload)
        bot_reply = res.json()['choices'][0]['message']['content']
        return jsonify({'reply': bot_reply})
    except Exception as e:
        return jsonify({'reply': "Protocol error, Sir. Check API Connection."})

@app.route('/get_history')
@login_required
def get_history():
    # Sidebar ke liye last 20 queries nikalna
    history = list(chat_db.find({"user_id": current_user.id}).sort("_id", -1).limit(20))
    formatted_history = [{"query": h['query']} for h in history]
    return jsonify({"history": formatted_history})

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == "__main__":
    # Render port handle karne ke liye
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
