from flask import Flask, request, jsonify, render_template
import requests
import datetime  # 🔥 Naya import date aur time ke liye

app = Flask(__name__)

# --- CONFIG ---
API_KEY = "AIzaSyCu-F44_ZunbgwXnB9JcmzCJIqLu1-EGDM" 

# Memory Store
chat_history = []

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    global chat_history
    data = request.json
    user_query = data.get('query')
    
    chat_history.append({"role": "user", "parts": [{"text": user_query}]})

    if len(chat_history) > 10:
        chat_history = chat_history[-10:]

    # 🔥 FIX: Aaj ki live date nikal kar AI ko batana
    aaj_ki_date = datetime.datetime.now().strftime("%d %B %Y")
    
    # System Instruction Update
    system_instruction = (
        f"You are an advanced PRO AI Assistant. Speak casually in Hinglish. "
        f"IMPORTANT: The current date is {aaj_ki_date}. "
        "Always provide answers, news, and context based on this current date. "
        "Remember previous context of the conversation. Keep answers helpful, crisp, and smart."
    )
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key={API_KEY}"
    
    payload = {
        "contents": chat_history,
        "system_instruction": {"parts": [{"text": system_instruction}]}
    }
    
    try:
        res = requests.post(url, headers={'Content-Type': 'application/json'}, json=payload)
        response_data = res.json()
        
        if 'candidates' in response_data:
            bot_reply = response_data['candidates'][0]['content']['parts'][0]['text'].strip()
            chat_history.append({"role": "model", "parts": [{"text": bot_reply}]})
            return jsonify({'reply': bot_reply})
        else:
            print("\n❌ API ERROR DETAILS:", response_data)
            chat_history.pop()
            return jsonify({'reply': "System Warning: API connection interrupted."})
            
    except requests.exceptions.RequestException as e:
        print("\n❌ CONNECTION ERROR:", e)
        chat_history.pop()
        return jsonify({'reply': "System Warning: Internet issue."})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
      
