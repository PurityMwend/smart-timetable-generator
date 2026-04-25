"""
Constraint Prediction Models.

Three specialized models to feed soft constraints into OR-Tools:
1. ConflictPredictor: Detects room/lecturer double-bookings
2. GapOptimizer: Predicts time gaps between courses
3. LoadBalancer: Predicts daily workload distribution
"""

import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from typing import Dict, List, Tuple, Any
import pickle
from pathlib import Path


class ConflictPredictor:
    """
    Predicts if a course assignment will cause conflicts.
    
    Binary classifier: 1 = conflict likely, 0 = no conflict
    Features: course_id, room_id, time_slot, lecturer_id, avg_load
    """
    
    def __init__(self, n_estimators=100, random_state=42):
        self.model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=15,
            random_state=random_state,
            n_jobs=-1,
        )
        self.scaler = StandardScaler()
        self.is_fitted = False
    
    def _extract_features(self, schedule: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Extract conflict indicators from timetable.
        
        Returns:
            (X_features, y_conflict_labels)
        """
        features = []
        labels = []
        
        entries = schedule.get('timetable_entries', [])
        courses = {str(c["id"]): c for c in schedule.get("courses", [])}
        rooms = {str(r["id"]): r for r in schedule.get("rooms", [])}
        
        # Count conflicts per entry
        for entry in entries:
            course_id = str(entry["course_id"])
            room_id = str(entry["room_id"])
            time_slot = entry.get('day', 0) * 288 + self._time_to_minutes(entry.get('start_time', '08:00')) // 5
            
            # Feature vector
            feature_vec = [
                course_id % 100,  # normalize
                room_id % 50,
                time_slot % 1000,
                courses.get(course_id, {}).get('class_size', 30),
                rooms.get(room_id, {}).get('capacity', 50),
            ]
            features.append(feature_vec)
            
            # Check if this entry causes conflicts
            # Count same room at same time
            same_room_time = sum(1 for e in entries 
                                if e['room_id'] == entry['room_id'] 
                                and e['day'] == entry['day']
                                and e['start_time'] == entry['start_time']
                                and e['course_id'] != course_id)
            
            # Count room capacity exceeded
            class_size = courses.get(course_id, {}).get('class_size', 30)
            room_capacity = rooms.get(room_id, {}).get('capacity', 50)
            capacity_exceeded = 1 if class_size > room_capacity else 0
            
            # Label: conflict if either condition met
            conflict = 1 if (same_room_time > 0 or capacity_exceeded) else 0
            labels.append(conflict)
        
        return np.array(features), np.array(labels)
    
    def _time_to_minutes(self, time_str: str) -> int:
        """Convert HH:MM to minutes since midnight."""
        try:
            h, m = map(int, time_str.split(':'))
            return h * 60 + m
        except:
            return 8 * 60
    
    def fit(self, schedules: List[Dict[str, Any]]):
        """Train conflict predictor."""
        all_X = []
        all_y = []
        
        for schedule in schedules:
            X, y = self._extract_features(schedule)
            if len(X) > 0:
                all_X.append(X)
                all_y.append(y)
        
        if not all_X:
            raise ValueError("No training data extracted")
        
        X = np.vstack(all_X)
        y = np.hstack(all_y)
        
        X = self.scaler.fit_transform(X)
        self.model.fit(X, y)
        self.is_fitted = True
        
        train_score = self.model.score(X, y)
        print(f"✓ ConflictPredictor training accuracy: {train_score:.3f}")
    
    def predict_conflict_risk(self, course_id: int, room_id: int, 
                             time_slot: int, class_size: int = 30, 
                             room_capacity: int = 50) -> float:
        """
        Predict conflict risk (0-1, higher = more likely).
        
        Returns probability of conflict.
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted")
        
        features = np.array([[
            course_id % 100,
            room_id % 50,
            time_slot % 1000,
            class_size,
            room_capacity,
        ]])
        
        features = self.scaler.transform(features)
        proba = self.model.predict_proba(features)[0]
        return proba[1]  # Probability of conflict
    
    def save(self, path: str):
        """Save model."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        data = {
            'model': self.model,
            'scaler': self.scaler,
            'is_fitted': self.is_fitted,
        }
        with open(path, 'wb') as f:
            pickle.dump(data, f)
        print(f"✓ ConflictPredictor saved to {path}")
    
    @staticmethod
    def load(path: str) -> 'ConflictPredictor':
        """Load model."""
        with open(path, 'rb') as f:
            data = pickle.load(f)
        predictor = ConflictPredictor()
        predictor.model = data['model']
        predictor.scaler = data['scaler']
        predictor.is_fitted = data['is_fitted']
        return predictor


class GapOptimizer:
    """
    Predicts optimal time gaps between courses for same lecturer/student.
    
    Regression model: predicts ideal minutes between consecutive courses.
    """
    
    def __init__(self, n_estimators=100, random_state=42):
        self.model = GradientBoostingRegressor(
            n_estimators=n_estimators,
            learning_rate=0.1,
            max_depth=5,
            random_state=random_state,
        )
        self.scaler = StandardScaler()
        self.is_fitted = False
    
    def _extract_features(self, schedule: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray]:
        """Extract gap patterns from timetable."""
        features = []
        gaps = []
        
        entries = schedule.get('timetable_entries', [])
        if len(entries) < 2:
            return np.array([]), np.array([])
        
        # Sort by lecturer and time
        entries_sorted = sorted(entries, key=lambda e: (e.get('lecturer_id', 0), e.get('day', 0), e.get('start_time', '')))
        
        for i in range(len(entries_sorted) - 1):
            curr = entries_sorted[i]
            next_entry = entries_sorted[i + 1]
            
            if curr.get('lecturer_id') != next_entry.get('lecturer_id'):
                continue
            
            # Calculate gap in minutes
            gap_minutes = self._calculate_gap(curr, next_entry)
            
            # Features
            feature_vec = [
                curr.get('day', 0),
                next_entry.get('day', 0),
                self._time_to_minutes(curr.get('start_time', '08:00')),
                self._time_to_minutes(next_entry.get('start_time', '08:00')),
            ]
            
            features.append(feature_vec)
            gaps.append(max(0, gap_minutes))  # Target: gap in minutes
        
        return np.array(features), np.array(gaps)
    
    def _time_to_minutes(self, time_str: str) -> int:
        try:
            h, m = map(int, time_str.split(':'))
            return h * 60 + m
        except:
            return 8 * 60
    
    def _calculate_gap(self, entry1: Dict, entry2: Dict) -> int:
        """Calculate gap between two entries in minutes."""
        if entry1['day'] != entry2['day']:
            return 24 * 60  # Next day
        
        end_time1 = self._time_to_minutes(entry1.get('end_time', '09:00'))
        start_time2 = self._time_to_minutes(entry2.get('start_time', '08:00'))
        return max(0, start_time2 - end_time1)
    
    def fit(self, schedules: List[Dict[str, Any]]):
        """Train gap optimizer."""
        all_X = []
        all_y = []
        
        for schedule in schedules:
            X, y = self._extract_features(schedule)
            if len(X) > 0:
                all_X.append(X)
                all_y.append(y)
        
        if not all_X:
            print("⚠ No gap features for training")
            return
        
        X = np.vstack(all_X)
        y = np.hstack(all_y)
        
        X = self.scaler.fit_transform(X)
        self.model.fit(X, y)
        self.is_fitted = True
        
        train_score = self.model.score(X, y)
        print(f"✓ GapOptimizer training R² score: {train_score:.3f}")
    
    def predict_optimal_gap(self, day1: int, day2: int, 
                           start_min1: int, start_min2: int) -> float:
        """Predict optimal gap in minutes."""
        if not self.is_fitted:
            raise ValueError("Model not fitted")
        
        features = np.array([[day1, day2, start_min1, start_min2]])
        features = self.scaler.transform(features)
        return max(0, self.model.predict(features)[0])
    
    def save(self, path: str):
        """Save model."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        data = {
            'model': self.model,
            'scaler': self.scaler,
            'is_fitted': self.is_fitted,
        }
        with open(path, 'wb') as f:
            pickle.dump(data, f)
        print(f"✓ GapOptimizer saved to {path}")
    
    @staticmethod
    def load(path: str) -> 'GapOptimizer':
        """Load model."""
        with open(path, 'rb') as f:
            data = pickle.load(f)
        optimizer = GapOptimizer()
        optimizer.model = data['model']
        optimizer.scaler = data['scaler']
        optimizer.is_fitted = data['is_fitted']
        return optimizer


class LoadBalancer:
    """
    Predicts optimal daily load distribution.
    
    Regression model: predicts ideal course count per day (Mon-Fri).
    """
    
    def __init__(self, n_estimators=100, random_state=42):
        self.model = GradientBoostingRegressor(
            n_estimators=n_estimators,
            learning_rate=0.1,
            max_depth=5,
            random_state=random_state,
        )
        self.scaler = StandardScaler()
        self.is_fitted = False
    
    def _extract_features(self, schedule: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray]:
        """Extract daily load patterns."""
        entries = schedule.get('timetable_entries', [])
        
        # Count courses per day
        daily_counts = [0] * 7
        for entry in entries:
            day = entry.get('day', 0) % 7
            daily_counts[day] += 1
        
        # Features: total courses, std dev of distribution
        total_courses = len(entries)
        num_days_active = sum(1 for c in daily_counts if c > 0)
        
        features = np.array([[
            total_courses,
            num_days_active,
            np.std(daily_counts),
        ]])
        
        # Target: calculate balance metric (lower std = better balance)
        balance_score = 1.0 / (1.0 + np.std(daily_counts))
        
        return features, np.array([balance_score])
    
    def fit(self, schedules: List[Dict[str, Any]]):
        """Train load balancer."""
        all_X = []
        all_y = []
        
        for schedule in schedules:
            X, y = self._extract_features(schedule)
            all_X.append(X)
            all_y.append(y)
        
        if not all_X:
            raise ValueError("No training data")
        
        X = np.vstack(all_X)
        y = np.hstack(all_y)
        
        X = self.scaler.fit_transform(X)
        self.model.fit(X, y)
        self.is_fitted = True
        
        train_score = self.model.score(X, y)
        print(f"✓ LoadBalancer training R² score: {train_score:.3f}")
    
    def predict_balance_score(self, total_courses: int, 
                              num_days: int, daily_std: float) -> float:
        """
        Predict balance score (0-1, higher = better balanced).
        
        Returns balance metric.
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted")
        
        features = np.array([[total_courses, num_days, daily_std]])
        features = self.scaler.transform(features)
        return np.clip(self.model.predict(features)[0], 0, 1)
    
    def save(self, path: str):
        """Save model."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        data = {
            'model': self.model,
            'scaler': self.scaler,
            'is_fitted': self.is_fitted,
        }
        with open(path, 'wb') as f:
            pickle.dump(data, f)
        print(f"✓ LoadBalancer saved to {path}")
    
    @staticmethod
    def load(path: str) -> 'LoadBalancer':
        """Load model."""
        with open(path, 'rb') as f:
            data = pickle.load(f)
        balancer = LoadBalancer()
        balancer.model = data['model']
        balancer.scaler = data['scaler']
        balancer.is_fitted = data['is_fitted']
        return balancer
