from flask import Flask, request, jsonify, render_template
import requests
import os

app = Flask(__name__)

# --- Groq API Key Activated ---
API_KEY = "Gsk_D34bOOQLjVLGOuUxeW3JWGdyb3FYLlGpK2mpy3z1kV1FDJVFjWJ3"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    user_query = data.get('query')
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {
                "role": "system", 
                "content": "You are J.A.R.V.I.S., a witty, smart, and helpful AI assistant. You are helping a 19-year-old student who is preparing for UPSC (Political Science) and CDS (Air Force/Para SF). Speak in Hinglish (Hindi + English) like Tony Stark's assistant. Be motivating and sharp."
            },
            {"role": "user", "content": user_query}
        ]
    }
    
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=20)
        res_data = res.json()
        
        if 'choices' in res_data:
            bot_reply = res_data['choices'][0]['message']['content'].strip()
            return jsonify({'reply': bot_reply})
        else:
            return jsonify({'reply': "Sir, Groq engine mein kuch issue hai. Ek baar refresh kijiye!"})
            
    except Exception as e:
        return jsonify({'reply': "Connection busy hai sir, Jarvis is trying to reconnect... 🔄"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
