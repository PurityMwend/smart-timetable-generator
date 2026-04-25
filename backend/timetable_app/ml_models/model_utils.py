"""
Model utilities: Feature scaling, encoding, and preprocessing.
"""

import numpy as np
import pickle
from sklearn.preprocessing import StandardScaler, LabelEncoder
from typing import Dict, List, Tuple, Any
import os


class FeatureScaler:
    """Handles feature normalization and encoding for ML models."""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.is_fitted = False
    
    def fit(self, data: Dict[str, np.ndarray], categorical_cols: List[str]):
        """
        Fit scaler and encoders on data.
        
        Args:
            data: Dictionary with feature name -> numpy array
            categorical_cols: List of categorical column names
        """
        # Fit numerical scaler
        numerical_data = []
        numerical_cols = [k for k in data.keys() if k not in categorical_cols]
        
        for col in numerical_cols:
            numerical_data.append(data[col].reshape(-1, 1))
        
        if numerical_data:
            X_numerical = np.hstack(numerical_data)
            self.scaler.fit(X_numerical)
        
        # Fit label encoders for categorical data
        for col in categorical_cols:
            if col in data:
                le = LabelEncoder()
                le.fit(data[col].astype(str))
                self.label_encoders[col] = le
        
        self.is_fitted = True
    
    def transform(self, data: Dict[str, np.ndarray], categorical_cols: List[str]) -> np.ndarray:
        """Transform data using fitted scaler and encoders."""
        if not self.is_fitted:
            raise ValueError("Scaler not fitted. Call fit() first.")
        
        features = []
        numerical_cols = [k for k in data.keys() if k not in categorical_cols]
        
        # Scale numerical features
        for col in numerical_cols:
            scaled = self.scaler.transform(data[col].reshape(-1, 1))
            features.append(scaled)
        
        # Encode categorical features
        for col in categorical_cols:
            if col in data and col in self.label_encoders:
                encoded = self.label_encoders[col].transform(data[col].astype(str))
                features.append(encoded.reshape(-1, 1))
        
        return np.hstack(features) if features else np.array([])
    
    def fit_transform(self, data: Dict[str, np.ndarray], categorical_cols: List[str]) -> np.ndarray:
        """Fit and transform in one step."""
        self.fit(data, categorical_cols)
        return self.transform(data, categorical_cols)
    
    def save(self, path: str):
        """Save scaler to disk."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump(self, f)
    
    @staticmethod
    def load(path: str):
        """Load scaler from disk."""
        with open(path, 'rb') as f:
            return pickle.load(f)


class ModelUtils:
    """Utility functions for model training and validation."""
    
    @staticmethod
    def split_data(X: np.ndarray, y: np.ndarray, 
                   train_size: float = 0.7, 
                   val_size: float = 0.15,
                   test_size: float = 0.15,
                   random_state: int = 42) -> Tuple[Tuple, Tuple, Tuple]:
        """
        Split data into train, validation, and test sets.
        
        Returns:
            Tuple of ((X_train, y_train), (X_val, y_val), (X_test, y_test))
        """
        np.random.seed(random_state)
        indices = np.random.permutation(len(X))
        n = len(X)
        
        train_end = int(n * train_size)
        val_end = train_end + int(n * val_size)
        
        train_idx = indices[:train_end]
        val_idx = indices[train_end:val_end]
        test_idx = indices[val_end:]
        
        return (
            (X[train_idx], y[train_idx]),
            (X[val_idx], y[val_idx]),
            (X[test_idx], y[test_idx])
        )
    
    @staticmethod
    def encode_schedule(schedule: Dict[str, Any]) -> np.ndarray:
        """
        Encode a timetable schedule into feature vector.
        
        Features:
        - Course distribution across days
        - Room utilization
        - Time slot distribution
        - Lecturer load
        """
        features = []
        
        # Course distribution (7 days)
        for day in range(7):
            day_count = len([e for e in schedule.get('timetable_entries', []) 
                            if e.get('day') == day])
            features.append(day_count)
        
        # Room utilization
        total_entries = len(schedule.get('timetable_entries', []))
        features.append(total_entries)
        
        # Average lecturers per entry
        if total_entries > 0:
            avg_lecturers = len(schedule.get('lecturers', [])) / max(total_entries, 1)
            features.append(avg_lecturers)
        
        return np.array(features)
    
    @staticmethod
    def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """Calculate ML metrics."""
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
        
        return {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, zero_division=0),
            'recall': recall_score(y_true, y_pred, zero_division=0),
            'f1': f1_score(y_true, y_pred, zero_division=0),
        }
    
    @staticmethod
    def save_model(model, path: str):
        """Save model to disk."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump(model, f)
    
    @staticmethod
    def load_model(path: str):
        """Load model from disk."""
        with open(path, 'rb') as f:
            return pickle.load(f)
