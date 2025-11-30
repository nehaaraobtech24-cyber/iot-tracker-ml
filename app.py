from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import requests
import os
from datetime import datetime
from ml_detector import detector

app = Flask(__name__)
CORS(app)

# Thinger.io credentials (from Render environment)
THINGER_USER = os.getenv('THINGER_USER', 'your_username')
THINGER_DEVICE = os.getenv('THINGER_DEVICE', 'your_device')
THINGER_TOKEN = os.getenv('THINGER_TOKEN', 'your_token')

# IMPORTANT: use the same regional API host as your device token's "svr".
# For your account it was "ap-southeast.aws.thinger.io" — change here if different.
THINGER_API_BASE = os.getenv('THINGER_API_BASE', 'https://ap-southeast.aws.thinger.io/v3')

@app.route('/')
def home():
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return jsonify({
            'status': 'IoT Location Tracker API with ML',
            'message': 'HTML file not found',
            'ml_stats': detector.get_stats(),
            'endpoints': {
                '/api/location': 'Get GPS location',
                '/api/gps-status': 'Get GPS status and satellites',
                '/api/led/<state>': 'Control LED (on/off)',
                '/api/buzzer/<state>': 'Control Buzzer (on/off)',
                '/api/ml/stats': 'Get ML model statistics',
                '/api/ml/check': 'Check if location is anomalous'
            }
        })

@app.route('/api/location')
def get_location():
    """Get GPS location from Thinger.io (uses gps_location resource)"""
    try:
        url = f'{THINGER_API_BASE}/users/{THINGER_USER}/devices/{THINGER_DEVICE}/resources/gps_location'
        headers = {'Authorization': f'Bearer {THINGER_TOKEN}'}

        response = requests.get(url, headers=headers, timeout=5)

        if response.status_code == 200 and response.content:
            data = response.json()

            # Thinger gps_location returns keys 'latitude' and 'longitude'
            lat = data.get('latitude') if isinstance(data, dict) else None
            lon = data.get('longitude') if isinstance(data, dict) else None

            # fallback if payload uses different keys
            if lat is None and data.get('lat') is not None:
                lat = data.get('lat')
            if lon is None and data.get('lon') is not None:
                lon = data.get('lon')

            try:
                lat = float(lat)
                lon = float(lon)
            except Exception:
                # malformed or missing GPS data -> use synthetic fallback
                lat, lon = None, None

            if lat is not None and lon is not None:
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

        # On any failure, return synthetic demo data
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

    except Exception:
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


@app.route('/api/gps-status')
def get_gps_status():
    """Get GPS status and satellite information (uses gps_status resource)"""
    try:
        url = f'{THINGER_API_BASE}/users/{THINGER_USER}/devices/{THINGER_DEVICE}/resources/gps_status'
        headers = {'Authorization': f'Bearer {THINGER_TOKEN}'}

        response = requests.get(url, headers=headers, timeout=5)

        if response.status_code == 200 and response.content:
            data = response.json()
            # if the device returns a structured object, pass it through
            if isinstance(data, dict):
                return jsonify({'success': True, 'gps_status': data})
            # otherwise, wrap string values
            return jsonify({'success': True, 'gps_status': {'status': data}})

        # fallback mock
        return jsonify({
            'success': True,
            'gps_status': {
                'fix': True,
                'satellites': 8,
                'hdop': 1.2,
                'satellite_list': [1, 3, 6, 11, 14, 17, 19, 28]
            }
        })

    except Exception:
        return jsonify({
            'success': True,
            'gps_status': {
                'fix': True,
                'satellites': 8,
                'hdop': 1.2,
                'satellite_list': [1, 3, 6, 11, 14, 17, 19, 28]
            }
        })


@app.route('/api/led/<state>')
def control_led(state):
    """Control LED - state can be 'on' or 'off'"""
    try:
        if state not in ['on', 'off']:
            return jsonify({'success': False, 'error': 'State must be "on" or "off"'}), 400

        url = f'{THINGER_API_BASE}/users/{THINGER_USER}/devices/{THINGER_DEVICE}/resources/led'
        headers = {
            'Authorization': f'Bearer {THINGER_TOKEN}',
            'Content-Type': 'application/json'
        }

        # send raw boolean (true/false) so Arduino receives a boolean pson
        payload = True if state == 'on' else False
        response = requests.post(url, headers=headers, json=payload, timeout=5)

        if response.status_code not in (200, 204):
            # include Thinger response text for diagnostics if needed
            return jsonify({'success': False, 'error': 'Thinger API error', 'code': response.status_code, 'body': response.text}), 500

        return jsonify({'success': True, 'message': f'LED turned {state}', 'state': state})

    except Exception as e:
        # simulated fallback (useful for demo when Thinger unreachable)
        return jsonify({'success': True, 'message': f'LED turned {state} (simulated)', 'state': state})


@app.route('/api/buzzer/<state>')
def control_buzzer(state):
    """Control Buzzer - state can be 'on' or 'off'"""
    try:
        if state not in ['on', 'off']:
            return jsonify({'success': False, 'error': 'State must be "on" or "off"'}), 400

        url = f'{THINGER_API_BASE}/users/{THINGER_USER}/devices/{THINGER_DEVICE}/resources/buzzer'
        headers = {
            'Authorization': f'Bearer {THINGER_TOKEN}',
            'Content-Type': 'application/json'
        }

        payload = True if state == 'on' else False
        response = requests.post(url, headers=headers, json=payload, timeout=5)

        if response.status_code not in (200, 204):
            return jsonify({'success': False, 'error': 'Thinger API error', 'code': response.status_code, 'body': response.text}), 500

        return jsonify({'success': True, 'message': f'Buzzer turned {state}', 'state': state})

    except Exception as e:
        return jsonify({'success': True, 'message': f'Buzzer turned {state} (simulated)', 'state': state})


@app.route('/api/ml/stats')
def ml_stats():
    """Get ML model statistics"""
    return jsonify(detector.get_stats())


@app.route('/api/ml/check', methods=['POST'])
def check_anomaly():
    """Check if a specific location is anomalous"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON provided'}), 400

        lat = data.get('lat')
        lon = data.get('lon')

        if lat is None or lon is None:
            return jsonify({'success': False, 'error': 'lat and lon are required'}), 400

        result = detector.predict(float(lat), float(lon), datetime.now())

        return jsonify({'success': True, 'result': result})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
