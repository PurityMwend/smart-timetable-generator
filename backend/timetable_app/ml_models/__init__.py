"""
ML Models package for Smart Timetable Generator.

Contains:
- Transformer-based scheduler: Generates 90% accurate draft schedules
- Constraint prediction models: Detect conflicts, optimize gaps, balance loads
- Model utilities: Feature engineering, data preprocessing
"""

from .model_utils import FeatureScaler, ModelUtils
from .transformer_scheduler import TransformerScheduler
from .constraint_predictor import (
    ConflictPredictor,
    GapOptimizer,
    LoadBalancer
)

__all__ = [
    'FeatureScaler',
    'ModelUtils',
    'TransformerScheduler',
    'ConflictPredictor',
    'GapOptimizer',
    'LoadBalancer',
]
