import numpy as np
from sklearn.ensemble import IsolationForest
from datetime import datetime
import json

class LocationAnomalyDetector:
    def __init__(self):
        self.model = IsolationForest(
            contamination=0.1,
            random_state=42
        )
        self.is_trained = False
        self.location_history = []
        
    def add_location(self, lat, lon, timestamp=None):
        """Add a location point to history"""
        if timestamp is None:
            timestamp = datetime.now()
        
        self.location_history.append({
            'lat': lat,
            'lon': lon,
            'timestamp': timestamp,
            'hour': timestamp.hour,
            'day_of_week': timestamp.weekday()
        })
        
        if len(self.location_history) >= 20 and not self.is_trained:
            self.train()
    
    def calculate_speed(self, loc1, loc2):
        """Calculate speed between two points (km/h)"""
        lat1, lon1 = loc1['lat'], loc1['lon']
        lat2, lon2 = loc2['lat'], loc2['lon']
        
        R = 6371
        
        dlat = np.radians(lat2 - lat1)
        dlon = np.radians(lon2 - lon1)
        a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        distance = R * c
        
        time_diff = (loc2['timestamp'] - loc1['timestamp']).total_seconds() / 3600
        
        if time_diff == 0:
            return 0
        
        return distance / time_diff
    
    def extract_features(self, location):
        """Extract features from a location point"""
        features = [
            location['lat'],
            location['lon'],
            location['hour'],
            location['day_of_week']
        ]
        
        if len(self.location_history) > 1:
            speed = self.calculate_speed(self.location_history[-2], location)
            features.append(speed)
        else:
            features.append(0)
        
        return features
    
    def train(self):
        """Train the anomaly detection model"""
        if len(self.location_history) < 20:
            return False
        
        X = np.array([self.extract_features(loc) for loc in self.location_history])
        
        self.model.fit(X)
        self.is_trained = True
        
        return True
    
    def predict(self, lat, lon, timestamp=None):
        """Predict if a location is anomalous"""
        if not self.is_trained:
            return {
                'is_anomaly': False,
                'confidence': 0,
                'reason': 'Model not trained yet (need 20+ data points)',
                'data_points': len(self.location_history)
            }
        
        if timestamp is None:
            timestamp = datetime.now()
        
        location = {
            'lat': lat,
            'lon': lon,
            'timestamp': timestamp,
            'hour': timestamp.hour,
            'day_of_week': timestamp.weekday()
        }
        
        features = np.array([self.extract_features(location)])
        
        prediction = self.model.predict(features)[0]
        
        score = self.model.score_samples(features)[0]
        confidence = abs(score)
        
        reason = "Normal behavior"
        if prediction == -1:
            if len(self.location_history) > 1:
                speed = self.calculate_speed(self.location_history[-1], location)
                if speed > 100:
                    reason = f"Unusually high speed detected: {speed:.1f} km/h"
                elif location['hour'] < 6 or location['hour'] > 23:
                    reason = "Movement at unusual time"
                else:
                    reason = "Location pattern is unusual"
        
        return {
            'is_anomaly': prediction == -1,
            'confidence': float(confidence),
            'reason': reason,
            'data_points': len(self.location_history)
        }
    
    def get_stats(self):
        """Get statistics about the detector"""
        return {
            'is_trained': self.is_trained,
            'total_points': len(self.location_history),
            'points_needed': max(0, 20 - len(self.location_history))
        }


detector = LocationAnomalyDetector()