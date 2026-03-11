import requests
import json
import os
from core.logger_config import logger

def send_embed(webhook_url, payload):
    """
    Mengirim payload embed ke Discord via Webhook.
    """
    try:
        response = requests.post(
            webhook_url,
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )
        if response.status_code in [200, 204]:
            logger.info("Embed berhasil dikirim ke Discord.")
            return True, "Berhasil dikirim!"
        else:
            logger.error(f"Gagal mengirim embed: {response.status_code} - {response.text}")
            return False, f"Error {response.status_code}: {response.text}"
    except Exception as e:
        logger.error(f"Kesalahan koneksi Webhook: {e}")
        return False, str(e)
