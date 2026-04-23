import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
import logging

logging.basicConfig(level=logging.INFO)

def send_alert(message):
    """ارسال هشدار به تلگرام"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": f"🚨 *Server Monitor Alert* 🚨\n\n{message}",
            "parse_mode": "Markdown"
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            logging.info("Alert sent to Telegram successfully")
        else:
            logging.error(f"Failed to send alert: {response.text}")
            
    except Exception as e:
        logging.error(f"Error sending alert: {e}")

def send_status_report(report):
    """ارسال گزارش وضعیت"""
    message = f"""
📊 *Server Status Report*

🖥️ *CPU:* {report['cpu']}%
💾 *RAM:* {report['ram']}%
⏰ *Uptime:* {report['uptime']}
📍 *Status:* {report['status']}
    """
    send_alert(message)

if __name__ == "__main__":
    send_alert("✅ Server Monitor is now active!")