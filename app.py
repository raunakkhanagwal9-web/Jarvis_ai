from flask import Flask, request, jsonify, render_template
import requests
import os

app = Flask(__name__)

# Render settings se key uthayega
API_KEY = os.environ.get("GROQ_API_KEY")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    user_query = data.get('query')
    
    if not API_KEY:
        return jsonify({'reply': "Sir, Key missing hai. Render settings check kijiye!"})

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "You are J.A.R.V.I.S., a witty and smart AI assistant. Speak in Hinglish like Tony Stark's assistant. Be helpful and cool."},
            {"role": "user", "content": user_query}
        ]
    }
    
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=20)
        res_data = res.json()
        if 'choices' in res_data:
            return jsonify({'reply': res_data['choices'][0]['message']['content'].strip()})
        else:
            return jsonify({'reply': "Sir, Groq engine mein kuch issue hai. Ek baar refresh kijiye!"})
    except Exception as e:
        return jsonify({'reply': "Connection busy hai sir!"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
