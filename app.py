from flask import Flask, request, jsonify, render_template
import requests
import datetime
import time

app = Flask(__name__)

# --- CONFIG ---
API_KEY = "AIzaSyCu-F44_ZunbgwXnB9JcmzCJIqLu1-EGDM" 

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

    aaj_ki_date = datetime.datetime.now().strftime("%d %B %Y")
    
    system_instruction = (
        f"You are an advanced PRO AI Assistant named J.A.R.V.I.S. Speak casually in Hinglish. "
        f"IMPORTANT: The current date is {aaj_ki_date}. Always provide context based on this date. "
        "Remember previous conversation. Be helpful, witty, and smart like Tony Stark's assistant."
    )
    
    # 🔥 Updated URL for better stability
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    
    payload = {
        "contents": chat_history,
        "system_instruction": {"parts": [{"text": system_instruction}]}
    }
    
    # Retry Logic: Agar ek baar fail ho toh dubara try karega
    for attempt in range(2):
        try:
            res = requests.post(url, headers={'Content-Type': 'application/json'}, json=payload, timeout=10)
            response_data = res.json()
            
            if 'candidates' in response_data:
                bot_reply = response_data['candidates'][0]['content']['parts'][0]['text'].strip()
                chat_history.append({"role": "model", "parts": [{"text": bot_reply}]})
                return jsonify({'reply': bot_reply})
            else:
                print(f"Attempt {attempt+1} fail: {response_data}")
                time.sleep(1) # 1 second wait karke dubara try
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)

    return jsonify({'reply': "System Warning: Connection weak hai sir, ek baar phir se try kijiye! ⚡"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
    
