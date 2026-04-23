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
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.config['SECRET_KEY'] = 'jarvis_secret_protocol_777'

# --- MONGODB CLOUD SETUP ---
# ⚠️ Yahan apna asli password dalo <db_password> ki jagah
app.config["MONGO_URI"] = "app.config["MONGO_URI"] = "mongodb+srv://raunakkhanagwal9_db_user:52Cqed7w1hCkE4xt@cluster0.czmwhtn.mongodb.net/jarvis_db?retryWrites=true&w=majority&appName=Cluster0"
"
mongo = PyMongo(app)
db = mongo.db.users # Users collection

# --- LOGIN MANAGER ---
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.email = user_data['email']
        self.username = user_data['username']

@login_manager.user_loader
def load_user(user_id):
    user_data = db.find_one({"_id": ObjectId(user_id)})
    return User(user_data) if user_data else None

# --- GOOGLE OAUTH SETUP ---
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id='869230187120-5531gadmiu9arhb2nsi9p5dkdqqj7elf.apps.googleusercontent.com',
    client_secret='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',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# --- ROUTES ---
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
            user_obj = User(user_data)
            login_user(user_obj)
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
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/ask', methods=['POST'])
@login_required
def ask():
    data = request.json
    query = data.get('query')
    API_KEY = os.environ.get("GROQ_API_KEY")
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "system", "content": f"You are J.A.R.V.I.S. User is {current_user.username} Sir."}] + [{"role": "user", "content": query}]
    }
    try:
        res = requests.post(url, headers=headers, json=payload)
        return jsonify({'reply': res.json()['choices'][0]['message']['content']})
    except:
        return jsonify({'reply': "Protocol error, Sir."})

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
        
