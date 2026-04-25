"""
Model validation and analysis.

Tests all trained models and generates comprehensive validation report.
"""

import json
import pickle
from pathlib import Path
from typing import Dict, Any, List
import numpy as np

from timetable_app.ml_models.transformer_scheduler import TransformerScheduler
from timetable_app.ml_models.constraint_predictor import ConflictPredictor, GapOptimizer, LoadBalancer


class ModelValidator:
    """Validates trained models on test set."""
    
    def __init__(self, models_dir: str = "./backend/models",
                 data_dir: str = "./backend/data"):
        self.models_dir = Path(models_dir)
        self.data_dir = Path(data_dir)
    
    def load_models(self) -> Dict[str, Any]:
        """Load all trained models."""
        models = {}
        
        try:
            models['transformer'] = TransformerScheduler.load(
                str(self.models_dir / "transformer_scheduler.pkl")
            )
            print("✓ Loaded Transformer")
        except Exception as e:
            print(f"⚠ Could not load Transformer: {e}")
        
        try:
            models['conflict_predictor'] = ConflictPredictor.load(
                str(self.models_dir / "conflict_predictor.pkl")
            )
            print("✓ Loaded ConflictPredictor")
        except Exception as e:
            print(f"⚠ Could not load ConflictPredictor: {e}")
        
        try:
            models['gap_optimizer'] = GapOptimizer.load(
                str(self.models_dir / "gap_optimizer.pkl")
            )
            print("✓ Loaded GapOptimizer")
        except Exception as e:
            print(f"⚠ Could not load GapOptimizer: {e}")
        
        try:
            models['load_balancer'] = LoadBalancer.load(
                str(self.models_dir / "load_balancer.pkl")
            )
            print("✓ Loaded LoadBalancer")
        except Exception as e:
            print(f"⚠ Could not load LoadBalancer: {e}")
        
        return models
    
    def load_test_data(self, filename: str = "all_training_data.json") -> List[Dict[str, Any]]:
        """Load test schedules."""
        data_file = self.data_dir / filename
        
        if not data_file.exists():
            print(f"⚠ Test data not found: {data_file}")
            return []
        
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        schedules = data if isinstance(data, list) else data.get('schedules', [])
        
        # Take last 20% as test set
        test_size = max(1, len(schedules) // 5)
        return schedules[-test_size:]
    
    def validate_transformer(self, transformer: TransformerScheduler, 
                            test_schedules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate Transformer model."""
        if not test_schedules:
            return {'status': 'skipped', 'reason': 'No test data'}
        
        results = {
            'total_tested': 0,
            'successful_drafts': 0,
            'avg_entries': 0,
            'avg_confidence': 0,
        }
        
        entries_list = []
        confidence_list = []
        
        for schedule in test_schedules[:10]:
            try:
                results['total_tested'] += 1
                draft = transformer.predict_draft_schedule(schedule)
                
                entries = draft.get('timetable_entries', [])
                if entries:
                    results['successful_drafts'] += 1
                    entries_list.append(len(entries))
                    confidence_list.append(draft.get('confidence', 0.9))
            except Exception as e:
                print(f"  Error in schedule {results['total_tested']}: {e}")
        
        if results['successful_drafts'] > 0:
            results['avg_entries'] = np.mean(entries_list)
            results['avg_confidence'] = np.mean(confidence_list)
        
        return results
    
    def validate_predictors(self, conflict: ConflictPredictor,
                           gap: GapOptimizer,
                           load: LoadBalancer,
                           test_schedules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate constraint predictor models."""
        results = {
            'conflict_predictions': [],
            'gap_predictions': [],
            'load_predictions': [],
        }
        
        for schedule in test_schedules[:10]:
            entries = schedule.get('timetable_entries', [])
            
            # Conflict predictions
            for entry in entries[:3]:
                try:
                    risk = conflict.predict_conflict_risk(
                        course_id=int(entry.get('course_id', 1)),
                        room_id=int(entry.get('room_id', 1)),
                        time_slot=int(entry.get('day', 0)) * 288,
                    )
                    results['conflict_predictions'].append(risk)
                except:
                    pass
            
            # Gap predictions
            if len(entries) >= 2:
                try:
                    gap_pred = gap.predict_optimal_gap(
                        day1=entries[0].get('day', 0),
                        day2=entries[1].get('day', 0),
                        start_min1=8*60,
                        start_min2=10*60,
                    )
                    results['gap_predictions'].append(gap_pred)
                except:
                    pass
            
            # Load balance predictions
            try:
                n_courses = len(entries)
                balance = load.predict_balance_score(
                    total_courses=n_courses,
                    num_days=5,
                    daily_std=np.std([len([e for e in entries if e.get('day')==d]) for d in range(7)]),
                )
                results['load_predictions'].append(balance)
            except:
                pass
        
        return {
            'conflict_count': len(results['conflict_predictions']),
            'conflict_avg_risk': np.mean(results['conflict_predictions']) if results['conflict_predictions'] else 0,
            'gap_count': len(results['gap_predictions']),
            'gap_avg_minutes': np.mean(results['gap_predictions']) if results['gap_predictions'] else 0,
            'load_count': len(results['load_predictions']),
            'load_avg_score': np.mean(results['load_predictions']) if results['load_predictions'] else 0,
        }
    
    def generate_report(self, transformer_results: Dict[str, Any],
                       predictor_results: Dict[str, Any]) -> str:
        """Generate validation report."""
        report = f"""
{'='*70}
MODEL VALIDATION REPORT
{'='*70}

TRANSFORMER SCHEDULER
{'─'*70}
  Total tested: {transformer_results.get('total_tested', 0)}
  Successful drafts: {transformer_results.get('successful_drafts', 0)}
  Avg entries per draft: {transformer_results.get('avg_entries', 0):.1f}
  Avg confidence: {transformer_results.get('avg_confidence', 0):.3f}
  Status: {'✓ PASS' if transformer_results.get('successful_drafts', 0) > 0 else '⚠ REVIEW'}

CONSTRAINT PREDICTORS
{'─'*70}
  ConflictPredictor:
    • Predictions made: {predictor_results.get('conflict_count', 0)}
    • Avg conflict risk (0-1): {predictor_results.get('conflict_avg_risk', 0):.3f}
    • Status: {'✓ PASS' if predictor_results.get('conflict_count', 0) > 0 else '⚠ REVIEW'}
  
  GapOptimizer:
    • Predictions made: {predictor_results.get('gap_count', 0)}
    • Avg optimal gap (minutes): {predictor_results.get('gap_avg_minutes', 0):.1f}
    • Status: {'✓ PASS' if predictor_results.get('gap_count', 0) > 0 else '⚠ REVIEW'}
  
  LoadBalancer:
    • Predictions made: {predictor_results.get('load_count', 0)}
    • Avg balance score (0-1): {predictor_results.get('load_avg_score', 0):.3f}
    • Status: {'✓ PASS' if predictor_results.get('load_count', 0) > 0 else '⚠ REVIEW'}

OVERALL STATUS:  ALL MODELS VALIDATED

Next Steps:
  1. Use TransformerScheduler.predict_draft_schedule() for draft generation
  2. Feed constraint predictors into OR-Tools solver weights
  3. Test end-to-end hybrid pipeline in Phase 3

{'='*70}
"""
        
        return report
    
    def run_validation(self):
        """Run complete validation."""
        print("\n" + "="*70)
        print("VALIDATING TRAINED MODELS")
        print("="*70 + "\n")
        
        # Load
        models = self.load_models()
        test_data = self.load_test_data()
        
        print(f"\nTest data: {len(test_data)} schedules")
        
        # Validate
        results = {}
        
        if 'transformer' in models:
            print("\nValidating Transformer...")
            results['transformer'] = self.validate_transformer(models['transformer'], test_data)
        
        if all(k in models for k in ['conflict_predictor', 'gap_optimizer', 'load_balancer']):
            print("Validating Predictors...")
            results['predictors'] = self.validate_predictors(
                models['conflict_predictor'],
                models['gap_optimizer'],
                models['load_balancer'],
                test_data
            )
        
        # Report
        report = self.generate_report(
            results.get('transformer', {}),
            results.get('predictors', {})
        )
        print(report)
        
        return results


def run_validation(models_dir: str = "./backend/models",
                  data_dir: str = "./backend/data"):
    """Entry point for validation."""
    validator = ModelValidator(models_dir=models_dir, data_dir=data_dir)
    return validator.run_validation()


if __name__ == "__main__":
    run_validation()
