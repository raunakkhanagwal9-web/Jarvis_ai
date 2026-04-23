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
# Render support ke liye
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.config['SECRET_KEY'] = 'jarvis_secret_protocol_777'

# --- ☁️ MONGODB CLOUD SETUP ---
app.config["MONGO_URI"] = "mongodb+srv://raunakkhanagwal9_db_user:52Cqed7w1hCkE4xt@cluster0.czmwhtn.mongodb.net/jarvis_db?retryWrites=true&w=majority&appName=Cluster0"
mongo = PyMongo(app)
db = mongo.db.users      
chat_db = mongo.db.chats 

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
        if not user_data or not check_password_hash(user_data['password'], password):
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
    email = user_info.get('email')
    user_data = db.find_one({"email": email})
    if not user_data:
        new_user = {"email": email, "username": user_info.get('name'), "password": generate_password_hash("google_bypass")}
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
        return redirect(url_for('login'))
    return render_template('register.html')

# --- 🧠 AI LOGIC (CHATGPT STYLE BEHAVIOUR) ---

@app.route('/ask', methods=['POST'])
@login_required
def ask():
    data = request.json
    query = data.get('query', '').strip()
    
    if not query:
        return jsonify({'reply': "I'm listening, Sir."})

    # Memory Save
    chat_db.insert_one({"user_id": current_user.id, "query": query})

    API_KEY = os.environ.get("GROQ_API_KEY")
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    
    # Context (Last 5 chats)
    history_data = list(chat_db.find({"user_id": current_user.id}).sort("_id", -1).limit(6))
    
    # 🔥 RAUNAK'S SPECIAL SYSTEM PROMPT (Human-like tone)
    system_prompt = (
        "You are J.A.R.V.I.S., a human-like AI assistant. "
        "Rules: 1. Reply in the user's language (Hindi, Hinglish, or English). "
        "2. Keep it natural and casual. No boring intros like 'It seems you are speaking Hindi'. "
        "3. Tone should be smart, clean, and helpful. "
        "4. Avoid robotic phrases. Use emojis like 🙂 or 🦾 occasionally. "
        "5. Keep answers concise unless asked for detail."
    )
    
    messages = [{"role": "system", "content": system_prompt}]
    for h in reversed(history_data):
        messages.append({"role": "user", "content": h['query']})

    try:
        res = requests.post(url, headers=headers, json={
            "model": "llama-3.3-70b-versatile", 
            "messages": messages,
            "temperature": 0.8,
            "max_tokens": 600
        })
        bot_reply = res.json()['choices'][0]['message']['content']

        # 🔥 CHATGPT STYLE FORMATTING (Paragraphs & Clean Spacing)
        # Multiple spaces aur unnecessary intro hatana
        bot_reply = bot_reply.replace(". ", ".\n\n").replace("! ", "!\n\n").replace("? ", "?\n\n")
        
        return jsonify({'reply': bot_reply.strip()})
    except:
        return jsonify({'reply': "Protocol error, Sir. Connection with neural core lost."})

@app.route('/get_history')
@login_required
def get_history():
    # Duplicate hatane ke liye logic
    history = list(chat_db.find({"user_id": current_user.id}).sort("_id", -1).limit(30))
    unique_queries = []
    seen = set()
    for h in history:
        clean_q = h['query'].strip()
        if clean_q not in seen:
            unique_queries.append({"query": clean_q})
            seen.add(clean_q)
    return jsonify({"history": unique_queries[:10]})

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
