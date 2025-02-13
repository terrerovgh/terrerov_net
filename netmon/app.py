from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import schedule
import threading
import time
import os
import json
import subprocess
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///network_monitor.db'
db = SQLAlchemy(app)

# Database Models
class NetworkScan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    scan_type = db.Column(db.String(50), nullable=False)
    target = db.Column(db.String(100), nullable=False)
    result = db.Column(db.Text, nullable=False)

class SpeedTest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    download_speed = db.Column(db.Float)
    upload_speed = db.Column(db.Float)
    ping = db.Column(db.Float)
    jitter = db.Column(db.Float)

class ErrorLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    error_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    ai_analysis = db.Column(db.Text)

# Network scanning functions
def run_nmap_scan(target):
    try:
        result = subprocess.run(['nmap', '-sV', target], capture_output=True, text=True)
        scan = NetworkScan(scan_type='nmap', target=target, result=result.stdout)
        db.session.add(scan)
        db.session.commit()
    except Exception as e:
        log_error('nmap_scan', str(e))

def run_speed_test():
    try:
        result = subprocess.run(['speedtest-cli', '--json'], capture_output=True, text=True)
        data = json.loads(result.stdout)
        test = SpeedTest(
            download_speed=data['download'] / 1_000_000,  # Convert to Mbps
            upload_speed=data['upload'] / 1_000_000,
            ping=data['ping'],
            jitter=data.get('jitter', 0)
        )
        db.session.add(test)
        db.session.commit()
    except Exception as e:
        log_error('speed_test', str(e))

def analyze_error_with_ai(error_type, description):
    try:
        api_key = os.getenv('DEEPSEEK_API_KEY')
        prompt = f"Analyze this network error and suggest solutions:\nType: {error_type}\nDescription: {description}"
        
        response = requests.post(
            'https://api.deepseek.com/v1/chat/completions',
            headers={'Authorization': f'Bearer {api_key}'},
            json={
                'model': 'deepseek-chat',
                'messages': [{'role': 'user', 'content': prompt}]
            }
        )
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"AI analysis failed: {str(e)}"

def log_error(error_type, description):
    ai_analysis = analyze_error_with_ai(error_type, description)
    error = ErrorLog(error_type=error_type, description=description, ai_analysis=ai_analysis)
    db.session.add(error)
    db.session.commit()

# Schedule tasks
def schedule_tasks():
    schedule.every(1).hour.do(run_nmap_scan, '172.20.0.0/16')
    schedule.every(30).minutes.do(run_speed_test)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/network-scans')
def get_network_scans():
    scans = NetworkScan.query.order_by(NetworkScan.timestamp.desc()).limit(10).all()
    return jsonify([{
        'timestamp': scan.timestamp,
        'scan_type': scan.scan_type,
        'target': scan.target,
        'result': scan.result
    } for scan in scans])

@app.route('/api/speed-tests')
def get_speed_tests():
    tests = SpeedTest.query.order_by(SpeedTest.timestamp.desc()).limit(24).all()
    return jsonify([{
        'timestamp': test.timestamp,
        'download_speed': test.download_speed,
        'upload_speed': test.upload_speed,
        'ping': test.ping,
        'jitter': test.jitter
    } for test in tests])

@app.route('/api/errors')
def get_errors():
    errors = ErrorLog.query.order_by(ErrorLog.timestamp.desc()).limit(10).all()
    return jsonify([{
        'timestamp': error.timestamp,
        'error_type': error.error_type,
        'description': error.description,
        'ai_analysis': error.ai_analysis
    } for error in errors])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    # Start scheduler in a separate thread
    scheduler_thread = threading.Thread(target=schedule_tasks)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    
    app.run(host='0.0.0.0', port=8000)