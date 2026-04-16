from flask import Flask, request, jsonify, render_template
import requests
import datetime

app = Flask(__name__)

# --- CONFIG ---
API_KEY = "AIzaSyCu-F44_ZunbgwXnB9JcmzCJIqLu1-EGDM" 

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    user_query = data.get('query')
    
    aaj_ki_date = datetime.datetime.now().strftime("%d %B %Y")
    
    # Ekdum simple structure taaki connection fast ho
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    
    payload = {
        "contents": [{
            "parts": [{"text": f"Date: {aaj_ki_date}. User says: {user_query}. Respond as Jarvis in Hinglish."}]
        }]
    }
    
    try:
        # Timeout badha kar 30 seconds kar diya hai
        res = requests.post(url, json=payload, timeout=30)
        response_data = res.json()
        
        if 'candidates' in response_data:
            bot_reply = response_data['candidates'][0]['content']['parts'][0]['text'].strip()
            return jsonify({'reply': bot_reply})
        else:
            return jsonify({'reply': "Sir, Google API ne mana kar diya. Key check kijiye! ⚡"})
            
    except Exception as e:
        return jsonify({'reply': "Network issue hai sir. Ek baar page Refresh karke try karein! 🔄"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
    
