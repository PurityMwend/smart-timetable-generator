"""
Create mock trained models for demonstration.

This creates dummy model files that allow Phase 4 validation to run end-to-end.
In production, these would be replaced by actually trained models.
"""

import pickle
import numpy as np
from pathlib import Path


class MockTransformerScheduler:
    """Mock transformer model for demonstration."""
    def __init__(self):
        self.is_trained = True
        self.model_version = "mock-v1"
    
    def predict_draft_schedule(self, schedule_template):
        """Return mock draft schedule."""
        num_courses = len(schedule_template.get('courses', []))
        num_slots = len(schedule_template.get('timeslots', []))
        num_rooms = len(schedule_template.get('rooms', []))
        
        return {
            'timetable_entries': [
                {
                    'course_id': i % num_courses,
                    'time_slot': i % num_slots,
                    'room_id': i % num_rooms,
                }
                for i in range(num_courses)
            ],
            'confidence': 0.87
        }


class MockConflictPredictor:
    """Mock conflict predictor model."""
    def __init__(self):
        self.is_trained = True
        self.model_version = "mock-v1"
    
    def predict_conflict_risk(self, course, room, time_slot):
        """Return mock conflict risk."""
        return np.random.uniform(0.1, 0.3)


class MockGapOptimizer:
    """Mock gap optimizer model."""
    def __init__(self):
        self.is_trained = True
        self.model_version = "mock-v1"
    
    def predict_optimal_gap(self, lecturer_schedule):
        """Return mock optimal gap in minutes."""
        return 30  # 30 minutes between courses


class MockLoadBalancer:
    """Mock load balancer model."""
    def __init__(self):
        self.is_trained = True
        self.model_version = "mock-v1"
    
    def predict_load_distribution(self, room_loads):
        """Return mock load balance score."""
        return 0.85


def create_mock_models(models_dir='./backend/models'):
    """Create and save mock trained models."""
    models_dir = Path(models_dir)
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # Create mock models
    models = {
        'transformer_scheduler.pkl': MockTransformerScheduler(),
        'conflict_predictor.pkl': MockConflictPredictor(),
        'gap_optimizer.pkl': MockGapOptimizer(),
        'load_balancer.pkl': MockLoadBalancer(),
    }
    
    # Save models
    for model_name, model in models.items():
        model_path = models_dir / model_name
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        print(f"✓ Created mock model: {model_path}")
    
    print(f"\n✓ Mock models created in {models_dir}")
    print("  Note: These are dummy models for demonstration.")
    print("  In production, use actual trained models from training_pipeline.py")
    
    return models_dir


if __name__ == '__main__':
    create_mock_models()
