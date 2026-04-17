from flask import Flask, request, jsonify, render_template
import requests
import os

app = Flask(__name__)

# Render ke Environment Variable se key uthayega
API_KEY = os.environ.get("GROQ_API_KEY")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    user_query = data.get('query')
    
    if not API_KEY:
        return jsonify({'reply': "Sir, API Key missing hai. Render settings check kijiye!"})

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "You are J.A.R.V.I.S., a witty AI assistant for a UPSC aspirant. Speak in Hinglish."},
            {"role": "user", "content": user_query}
        ]
    }
    
    try:
        # Timeout ko 30 seconds kar diya taaki slow network par fail na ho
        res = requests.post(url, headers=headers, json=payload, timeout=30)
        res_data = res.json()
        
        if 'choices' in res_data:
            bot_reply = res_data['choices'][0]['message']['content'].strip()
            return jsonify({'reply': bot_reply})
        else:
            # Asli error message print hoga taaki hum logs mein dekh sakein
            error_msg = res_data.get('error', {}).get('message', 'Unknown Error')
            print(f"Groq Error: {error_msg}")
            return jsonify({'reply': f"Sir, Groq error: {error_msg}"})
            
    except Exception as e:
        print(f"Python Error: {str(e)}")
        return jsonify({'reply': "Connection timeout! Ek baar phir try kijiye sir."})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
