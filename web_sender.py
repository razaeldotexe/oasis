import os
from flask import Flask, render_template, request, jsonify
from core.sender_logic import send_embed
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Tetapkan webhook default dari .env jika ada
DEFAULT_WEBHOOK = os.getenv('DISCORD_WEBHOOK_URL', '')

@app.route('/')
def index():
    return render_template('index.html', default_webhook=DEFAULT_WEBHOOK)

@app.route('/send', methods=['POST'])
def send():
    data = request.json
    webhook_url = data.get('webhook_url') or DEFAULT_WEBHOOK
    
    if not webhook_url:
        return jsonify({'success': False, 'message': 'Webhook URL tidak ditemukan!'}), 400

    # Konstruksi Payload Discord
    payload = {
        "embeds": [{
            "title": data.get('title'),
            "description": data.get('description'),
            "color": int(data.get('color', '3447003').replace('#', ''), 16),
            "image": {"url": data.get('image_url')} if data.get('image_url') else None,
            "footer": {"text": data.get('footer')} if data.get('footer') else None
        }]
    }

    success, message = send_embed(webhook_url, payload)
    return jsonify({'success': success, 'message': message})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
