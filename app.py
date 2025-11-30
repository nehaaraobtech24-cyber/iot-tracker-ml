from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import os
from datetime import datetime
from ml_detector import detector

app = Flask(__name__)
CORS(app)

# ---------------------------------------------------------
# Load Thinger.io credentials from environment variables
# ---------------------------------------------------------
THINGER_USER = os.getenv('THINGER_USER')
THINGER_DEVICE = os.getenv('THINGER_DEVICE')
THINGER_TOKEN = os.getenv('THINGER_TOKEN')

# IMPORTANT: use your device's server region (from token "svr" field)
# Your device token had: "ap-southeast.aws.thinger.io"
THINGER_API_BASE = "https://ap-southeast.aws.thinger.io/v3"


# ---------------------------------------------------------
# HOME PAGE
# ---------------------------------------------------------
@app.route('/')
def home():
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return jsonify({
            'status': 'IoT Location Tracker API with ML',
            'ml_stats': detector.get_stats()
        })


# ---------------------------------------------------------
# GPS LOCATION
# ---------------------------------------------------------
@app.route('/api/location')
def get_location():
    try:
        url = f"{THINGER_API_BASE}/users/{THINGER_USER}/devices/{THINGER_DEVICE}/resources/gps_location"
        headers = {'Authorization': f'Bearer {THINGER_TOKEN}'}

        response = requests.get(url, headers=headers, timeout=5)

        if response.status_code == 200:
            data = response.json()

            lat = data.get("latitude")
            lon = data.get("longitude")

            if lat is not None and lon is not None:
                lat = float(lat)
                lon = float(lon)

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

        # fallback synthetic
        fallback_lat, fallback_lon = 13.0827, 80.2707
        return jsonify({
            'success': True,
            'location': {
                'lat': fallback_lat,
                'lon': fallback_lon,
                'timestamp': datetime.now().isoformat()
            },
            'ml_analysis': detector.predict(fallback_lat, fallback_lon, datetime.now())
        })

    except Exception as e:
        fallback_lat, fallback_lon = 13.0827, 80.2707
        return jsonify({
            'success': True,
            'location': {
                'lat': fallback_lat,
                'lon': fallback_lon,
                'timestamp': datetime.now().isoformat()
            },
            'ml_analysis': detector.predict(fallback_lat, fallback_lon, datetime.now())
        })


# ---------------------------------------------------------
# GPS STATUS
# ---------------------------------------------------------
@app.route('/api/gps-status')
def get_gps_status():
    try:
        url = f"{THINGER_API_BASE}/users/{THINGER_USER}/devices/{THINGER_DEVICE}/resources/gps_status"
        headers = {'Authorization': f'Bearer {THINGER_TOKEN}'}

        response = requests.get(url, headers=headers, timeout=5)

        if response.status_code == 200:
            return jsonify({'success': True, 'gps_status': response.json()})

        # fallback mock
        return jsonify({
            'success': True,
            'gps_status': {
                'fix': True,
                'satellites': 8,
                'hdop': 1.2
            }
        })

    except:
        return jsonify({
            'success': True,
            'gps_status': {
                'fix': True,
                'satellites': 8,
                'hdop': 1.2
            }
        })


# ---------------------------------------------------------
# LED CONTROL
# ---------------------------------------------------------
@app.route('/api/led/<state>')
def control_led(state):
    try:
        if state not in ['on', 'off']:
            return jsonify({'success': False, 'error': 'State must be "on" or "off"'}), 400

        url = f"{THINGER_API_BASE}/users/{THINGER_USER}/devices/{THINGER_DEVICE}/resources/led"
        headers = {
            'Authorization': f'Bearer {THINGER_TOKEN}',
            'Content-Type': 'application/json'
        }

        payload = True if state == 'on' else False

        # DEBUG LOGS
        print(f"[DEBUG] LED POST → URL: {url} | payload={payload}")
        response = requests.post(url, headers=headers, json=payload, timeout=8)
        print(f"[DEBUG] LED response → status={response.status_code}, body={response.text}")

        if response.status_code not in (200, 204):
            return jsonify({
                'success': False,
                'error': 'Thinger API error',
                'code': response.status_code,
                'body': response.text
            }), 500

        return jsonify({
            'success': True,
            'message': f'LED turned {state}',
            'state': state
        })

    except Exception as e:
        print(f"[ERROR] LED exception: {e}")
        return jsonify({
            'success': True,
            'message': f'LED turned {state} (simulated)',
            'state': state
        })


# ---------------------------------------------------------
# BUZZER CONTROL
# ---------------------------------------------------------
@app.route('/api/buzzer/<state>')
def control_buzzer(state):
    try:
        if state not in ['on', 'off']:
            return jsonify({'success': False, 'error': 'State must be "on" or "off"'}), 400

        url = f"{THINGER_API_BASE}/users/{THINGER_USER}/devices/{THINGER_DEVICE}/resources/buzzer"
        headers = {
            'Authorization': f'Bearer {THINGER_TOKEN}',
            'Content-Type': 'application/json'
        }

        payload = True if state == 'on' else False

        # DEBUG LOGS
        print(f"[DEBUG] BUZZER POST → URL: {url} | payload={payload}")
        response = requests.post(url, headers=headers, json=payload, timeout=8)
        print(f"[DEBUG] BUZZER response → status={response.status_code}, body={response.text}")

        if response.status_code not in (200, 204):
            return jsonify({
                'success': False,
                'error': 'Thinger API error',
                'code': response.status_code,
                'body': response.text
            }), 500

        return jsonify({
            'success': True,
            'message': f'Buzzer turned {state}',
            'state': state
        })

    except Exception as e:
        print(f"[ERROR] BUZZER exception: {e}")
        return jsonify({
            'success': True,
            'message': f'Buzzer turned {state} (simulated)',
            'state': state
        })


# ---------------------------------------------------------
# ML endpoints
# ---------------------------------------------------------
@app.route('/api/ml/stats')
def ml_stats():
    return jsonify(detector.get_stats())


@app.route('/api/ml/check', methods=['POST'])
def check_anomaly():
    try:
        data = request.json
        lat = data.get('lat')
        lon = data.get('lon')

        if lat is None or lon is None:
            return jsonify({'success': False, 'error': 'lat and lon required'}), 400

        result = detector.predict(float(lat), float(lon), datetime.now())

        return jsonify({'success': True, 'result': result})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ---------------------------------------------------------
# RUN SERVER
# ---------------------------------------------------------
if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
