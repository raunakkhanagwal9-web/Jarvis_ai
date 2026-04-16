from flask import Flask, request, jsonify, render_template
import requests
import datetime
import os

app = Flask(__name__)

# --- Nayi API Key Fit Kar Di Hai ---
API_KEY = "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" 

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    user_query = data.get('query')
    
    aaj_ki_date = datetime.datetime.now().strftime("%d %B %Y")
    
    # URL for Gemini 1.5 Flash (Super Stable)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    
    # Clean Payload structure for Render Cloud
    payload = {
        "contents": [{
            "parts": [{"text": f"Today is {aaj_ki_date}. You are J.A.R.V.I.S., a witty and smart AI assistant for a UPSC/Defense aspirant. Answer the user in Hinglish: {user_query}"}]
        }]
    }
    
    try:
        # Increase timeout to 40 seconds to handle Render's slower network
        res = requests.post(url, json=payload, timeout=40)
        response_data = res.json()
        
        if 'candidates' in response_data:
            bot_reply = response_data['candidates'][0]['content']['parts'][0]['text'].strip()
            return jsonify({'reply': bot_reply})
        else:
            # Deep error logging for troubleshooting
            print("API Error Response:", response_data)
            return jsonify({'reply': "Sir, API connection mein kuch glitch hai. Ek baar refresh kijiye!"})
            
    except Exception as e:
        print("Request Exception:", e)
        return jsonify({'reply': "Network busy hai sir, please try again in a moment! 🔄"})

if __name__ == "__main__":
    # Render port configuration
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
