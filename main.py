import threading
import time
import schedule
from monitor import ServerMonitor
from web_dashboard import app
from config import CHECK_INTERVAL, WEB_HOST, WEB_PORT
import logging
import sys
import io

# تنظیم encoding برای ویندوز
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/monitor.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

def run_monitor():
    """اجرای مانیتورینگ در یک ترد جداگانه"""
    monitor = ServerMonitor()
    
    schedule.every(CHECK_INTERVAL).seconds.do(monitor.collect_all_metrics)
    
    print("[OK] Server monitor started")
    logging.info("Server monitor started")
    
    while True:
        schedule.run_pending()
        time.sleep(1)

def run_web():
    """اجرای وب سرور"""
    print(f"[OK] Web server started on http://{WEB_HOST}:{WEB_PORT}")
    logging.info(f"Web server started on http://{WEB_HOST}:{WEB_PORT}")
    app.run(host=WEB_HOST, port=WEB_PORT, debug=False, use_reloader=False)

if __name__ == "__main__":
    # اجرای مانیتورینگ در ترد جداگانه
    monitor_thread = threading.Thread(target=run_monitor, daemon=True)
    monitor_thread.start()
    
    # اجرای وب سرور
    run_web()