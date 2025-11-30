from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import os
from datetime import datetime
from ml_detector import detector

app = Flask(__name__)
CORS(app)

# Thinger.io credentials
THINGER_USER = os.getenv('THINGER_USER', 'your_username')
THINGER_DEVICE = os.getenv('THINGER_DEVICE', 'your_device')
THINGER_TOKEN = os.getenv('THINGER_TOKEN', 'your_token')

@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta http-equiv="refresh" content="0; url=/index.html">
    </head>
    <body>
        <p>Redirecting to dashboard...</p>
    </body>
    </html>
    '''

@app.route('/index.html')
def dashboard():
    with open('index.html', 'r') as f:
        return f.read()

@app.route('/api')
def api_info():
    return jsonify({
        'status': 'IoT Location Tracker API with ML',
@app.route('/api/location')
def get_location():
    """Get GPS location from Thinger.io"""
    try:
        url = f'https://api.thinger.io/v3/users/{THINGER_USER}/devices/{THINGER_DEVICE}/resources/location'
        headers = {'Authorization': f'Bearer {THINGER_TOKEN}'}
        
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            lat = data.get('lat', 0)
            lon = data.get('lon', 0)
            
            detector.add_location(lat, lon, datetime.now())
            ml_result = detector.predict(lat, lon, datetime.now())
            
            return jsonify({
                'success': True,
                'location': {
                    'lat': lat,
                    'lon': lon,
                    'timestamp': datetime.now().isoformat()
                },
                'ml_analysis': ml_result
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Thinger.io returned status {response.status_code}'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/gps-status')
def get_gps_status():
    """Get GPS status and satellite information"""
    try:
        url = f'https://api.thinger.io/v3/users/{THINGER_USER}/devices/{THINGER_DEVICE}/resources/gps_status'
        headers = {'Authorization': f'Bearer {THINGER_TOKEN}'}
        
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            return jsonify({
                'success': True,
                'gps_status': data
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Thinger.io returned status {response.status_code}'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/led/<state>')
def control_led(state):
    """Control LED - state can be 'on' or 'off'"""
    try:
        if state not in ['on', 'off']:
            return jsonify({
                'success': False,
                'error': 'State must be "on" or "off"'
            }), 400
        
        url = f'https://api.thinger.io/v3/users/{THINGER_USER}/devices/{THINGER_DEVICE}/resources/led'
        headers = {
            'Authorization': f'Bearer {THINGER_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        payload = {'state': state}
        response = requests.post(url, headers=headers, json=payload, timeout=5)
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'message': f'LED turned {state}',
                'state': state
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Thinger.io returned status {response.status_code}'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/buzzer/<state>')
def control_buzzer(state):
    """Control Buzzer - state can be 'on' or 'off'"""
    try:
        if state not in ['on', 'off']:
            return jsonify({
                'success': False,
                'error': 'State must be "on" or "off"'
            }), 400
        
        url = f'https://api.thinger.io/v3/users/{THINGER_USER}/devices/{THINGER_DEVICE}/resources/buzzer'
        headers = {
            'Authorization': f'Bearer {THINGER_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        payload = {'state': state}
        response = requests.post(url, headers=headers, json=payload, timeout=5)
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'message': f'Buzzer turned {state}',
                'state': state
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Thinger.io returned status {response.status_code}'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/ml/stats')
def ml_stats():
    """Get ML model statistics"""
    return jsonify(detector.get_stats())

@app.route('/api/ml/check', methods=['POST'])
def check_anomaly():
    """Check if a specific location is anomalous"""
    try:
        data = request.json
        lat = data.get('lat')
        lon = data.get('lon')
        
        if lat is None or lon is None:
            return jsonify({
                'success': False,
                'error': 'lat and lon are required'
            }), 400
        
        result = detector.predict(lat, lon, datetime.now())
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)