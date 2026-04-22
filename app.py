from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix  # NAYA IMPORT (Render Fix)
import requests
import os
from authlib.integrations.flask_client import OAuth

app = Flask(__name__)

# NAYA FIX: Render ke HTTPS issue ko solve karne ke liye
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

app.config['SECRET_KEY'] = 'jarvis_secret_protocol_101'

# Render-specific database path fix
db_path = os.path.join('/tmp', 'users.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User Table Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    username = db.Column(db.String(150), nullable=False)
    password = db.Column(db.String(150), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.before_request
def create_tables():
    db.create_all()

# --- GOOGLE OAUTH SETUP ---
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id='869230187120-5531gadmiu9arhb2nsi9p5dkdqqj7elf.apps.googleusercontent.com',     # <-- APNI ID WAPAS DAALO
    client_secret='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',    # <-- APNA SECRET WAPAS DAALO
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
        user = User.query.filter_by(email=email).first()
        
        if not user:
            flash('User not found, Sir.')
        elif not check_password_hash(user.password, password):
            flash('Invalid email/password, Sir.')
        else:
            login_user(user)
            return redirect(url_for('home'))
            
    return render_template('login.html')

# --- GOOGLE LOGIN ROUTES ---
@app.route('/login/google')
def google_login():
    # NAYA FIX: Zabardasti HTTPS par redirect karwana
    redirect_uri = url_for('google_authorize', _external=True, _scheme='https')
    return google.authorize_redirect(redirect_uri)

@app.route('/login/google/authorize')
def google_authorize():
    # Token receive karna
    token = google.authorize_access_token()
    
    # User ki details token se nikalna (Safe method)
    user_info = token.get('userinfo')
    if not user_info:
        resp = google.get('https://openidconnect.googleapis.com/v1/userinfo')
        user_info = resp.json()
    
    email = user_info.get('email')
    name = user_info.get('name', 'Jarvis User')

    # Check agar user pehle se hai
    user = User.query.filter_by(email=email).first()
    if not user:
        # Naya user create karo
        hashed_pw = generate_password_hash("google_oauth_bypass", method='pbkdf2:sha256')
        user = User(email=email, username=name, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
    
    login_user(user)
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email').strip()
        username = request.form.get('username').strip()
        password = request.form.get('password').strip()
        
        if len(password) < 6:
            flash('Password too short (Minimum 6 characters), Sir.')
            return redirect(url_for('register'))
            
        if User.query.filter_by(email=email).first():
            flash('Email already registered, Sir.')
            return redirect(url_for('register'))
            
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(email=email, username=username, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
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
        "messages": [
            {"role": "system", "content": f"You are J.A.R.V.I.S. User is {current_user.username} Sir. Speak witty Hinglish."}
        ] + [{"role": "user", "content": query}]
    }
    try:
        res = requests.post(url, headers=headers, json=payload)
        return jsonify({'reply': res.json()['choices'][0]['message']['content']})
    except:
        return jsonify({'reply': "Protocol error, Sir."})

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
