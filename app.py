hfrom flask import Flask, request, jsonify, render_template
import requests
import os

app = Flask(__name__)

# Render ki settings se API key lega
API_KEY = os.environ.get("GROQ_API_KEY")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    user_query = data.get('query')
    
    if not API_KEY:
        return jsonify({'reply': "Sir, API Key missing hai. Render ki settings mein check kijiye!"})

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
                "content": "You are J.A.R.V.I.S., a witty, loyal, and highly intelligent AI assistant. Speak in Hinglish (Hindi + English mix). Your tone should be cool and human-like, occasionally calling the user 'Sir' or 'Boss'. You are NOT a typical chatbot; you are a personal assistant like the one from Iron Man. Help with anything from daily tasks to coding and fun chats."
            },
            {"role": "user", "content": user_query}
        ]
    }
    
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=20)
        res_data = res.json()
        if 'choices' in res_data:
            return jsonify({'reply': res_data['choices'][0]['message']['content'].strip()})
        else:
            return jsonify({'reply': "Sir, Groq engine is busy. Please try again in a moment."})
    except Exception as e:
        return jsonify({'reply': "Connection busy hai, Sir!"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
