from flask import Flask, render_template, jsonify
from monitor import ServerMonitor
from config import WEB_HOST, WEB_PORT, DEBUG_MODE
import json
import os

app = Flask(__name__)
monitor = ServerMonitor()

@app.route('/')
def dashboard():
    """صفحه اصلی داشبورد"""
    return render_template('dashboard.html')

@app.route('/api/metrics')
def get_metrics():
    """API برای دریافت متریک‌ها"""
    metrics = monitor.collect_all_metrics()
    return jsonify(metrics)

@app.route('/api/summary')
def get_summary():
    """API برای دریافت خلاصه"""
    summary = monitor.get_summary()
    return jsonify(summary)

@app.route('/api/history')
def get_history():
    """API برای دریافت تاریخچه"""
    return jsonify(monitor.history[-50:])

@app.route('/api/alerts')
def get_alerts():
    """API برای دریافت هشدارها"""
    return jsonify(monitor.alerts[-20:])

if __name__ == '__main__':
    app.run(host=WEB_HOST, port=WEB_PORT, debug=DEBUG_MODE)