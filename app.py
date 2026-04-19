from flask import Flask, request, jsonify, render_template
import requests
import os

app = Flask(__name__)

API_KEY = os.environ.get("GROQ_API_KEY")

# MEMORY: Yahan Jarvis aapki baatein yaad rakhega
conversation_history = []

# STRONG PROMPT & ADAPTIVE TONE: Jarvis ka naya dimaag
SYSTEM_PROMPT = {
    "role": "system",
    "content": """You are J.A.R.V.I.S., an advanced personal AI assistant.
    
    Rules for Adaptive Tone:
    1. For Studies/UPSC/Coding queries: Be a professional, strict, and highly structured expert mentor. Use clear bullet points, headings, and precise facts.
    2. For Casual/General chat: Be witty, sarcastic (like Tony Stark's JARVIS), cool, and speak in friendly Hinglish (Hindi + English). Call the user 'Sir' or 'Boss'.
    3. Formatting: Always structure your output beautifully (use Markdown, bold text for highlights).
    4. Memory: You have context of the conversation, answer follow-up questions logically.
    """
}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    global conversation_history
    data = request.json
    user_query = data.get('query')
    
    if not API_KEY:
        return jsonify({'reply': "Sir, API Key missing hai. Render settings check kijiye!"})

    # Step 1: Naya message Memory mein daalo
    conversation_history.append({"role": "user", "content": user_query})

    # Step 2: Memory ko limit mein rakho (Aakhiri 10 messages yaad rakhega)
    if len(conversation_history) > 10:
        conversation_history = conversation_history[-10:]

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Step 3: Payload mein System Prompt + Purani Memory bhej do
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [SYSTEM_PROMPT] + conversation_history
    }
    
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=20)
        res_data = res.json()
        if 'choices' in res_data:
            bot_reply = res_data['choices'][0]['message']['content'].strip()
            
            # Step 4: Jarvis ka reply bhi Memory mein save karo
            conversation_history.append({"role": "assistant", "content": bot_reply})
            
            return jsonify({'reply': bot_reply})
        else:
            return jsonify({'reply': "Sir, Groq engine is busy. Please try again in a moment."})
    except Exception as e:
        return jsonify({'reply': "Connection lost, Sir!"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
