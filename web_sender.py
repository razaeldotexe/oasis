import os
from flask import Flask, render_template, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from core.sender_logic import send_embed
from core.logger_config import logger
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-key-12345')

# Rate Limiter: Maksimal 10 request per menit per IP
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["100 per day", "10 per minute"],
    storage_uri="memory://"
)

# Tetapkan webhook default dari .env jika ada
DEFAULT_WEBHOOK = os.getenv('DISCORD_WEBHOOK_URL', '')

@app.route('/')
def index():
    return render_template('index.html', default_webhook=DEFAULT_WEBHOOK)

@app.route('/send', methods=['POST'])
@limiter.limit("5 per minute") # Limit lebih ketat untuk pengiriman
def send():
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'message': 'Payload kosong!'}), 400
            
        webhook_url = data.get('webhook_url') or DEFAULT_WEBHOOK
        
        if not webhook_url or not webhook_url.startswith('https://discord.com/api/webhooks/'):
            return jsonify({'success': False, 'message': 'Webhook URL tidak valid!'}), 400

        # Konstruksi Payload Discord
        payload = {
            "embeds": [{
                "title": data.get('title', 'No Title')[:256], # Limit karakter Discord
                "description": data.get('description', '')[:4096],
                "color": int(data.get('color', '#3447003').replace('#', ''), 16),
                "image": {"url": data.get('image_url')} if data.get('image_url') else None,
                "footer": {"text": data.get('footer', '')[:2048]} if data.get('footer') else None
            }]
        }

        success, message = send_embed(webhook_url, payload)
        return jsonify({'success': success, 'message': message})
    except Exception as e:
        logger.error(f"Web Sender Error: {e}")
        return jsonify({'success': False, 'message': 'Terjadi kesalahan internal server.'}), 500

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({'success': False, 'message': 'Terlalu banyak permintaan. Silakan tunggu sebentar.'}), 429

if __name__ == '__main__':
    if not DEFAULT_WEBHOOK:
        logger.warning("DISCORD_WEBHOOK_URL belum dikonfigurasi di .env")
    app.run(host='0.0.0.0', port=5000)
