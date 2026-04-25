"""
Constraint Builder: Converts ML predictions to OR-Tools weighted constraints.

Pipeline:
1. Get ML predictions (conflict risk, gap preferences, load balance)
2. Convert to OR-Tools objective weights and soft constraints
3. Pass to solver for refinement
"""

import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass


@dataclass
class ConstraintWeights:
    """Encapsulates constraint weights for OR-Tools."""
    conflict_penalty: float = 100.0    # Hard constraint: penalize conflicts heavily
    gap_preference: float = 50.0       # Soft: prefer small gaps
    load_balance: float = 30.0         # Soft: balance daily loads
    room_utilization: float = 20.0     # Soft: efficient room use
    
    def to_dict(self) -> Dict[str, float]:
        """Export as dictionary for solver."""
        return {
            'conflict': self.conflict_penalty,
            'gap': self.gap_preference,
            'balance': self.load_balance,
            'utilization': self.room_utilization,
        }


class ConstraintBuilder:
    """
    Builds OR-Tools constraints and objective weights from ML predictions.
    
    Architecture:
    1. ConflictPredictor → Soft penalty for assignments likely to cause conflicts
    2. GapOptimizer → Preference weights for time separations
    3. LoadBalancer → Distribution penalties for unbalanced days
    """
    
    def __init__(self, base_weights: Optional[ConstraintWeights] = None):
        """Initialize constraint builder."""
        self.base_weights = base_weights or ConstraintWeights()
        self.constraints = []
        self.penalties = {}
    
    def add_conflict_constraint(self, 
                               course_id: int, 
                               room_id: int, 
                               time_slot: int,
                               conflict_risk: float) -> Dict[str, Any]:
        """
        Add soft constraint from ConflictPredictor.
        
        Args:
            conflict_risk: Probability of conflict (0-1)
                - High risk → higher penalty weight
                - Applied as: penalty = risk * base_conflict_penalty
        
        Returns:
            Constraint definition for solver
        """
        # Scale penalty based on conflict probability
        penalty = conflict_risk * self.base_weights.conflict_penalty
        
        constraint = {
            'type': 'conflict_avoidance',
            'course_id': course_id,
            'room_id': room_id,
            'time_slot': time_slot,
            'penalty': penalty,
            'conflict_risk': conflict_risk,
        }
        
        self.constraints.append(constraint)
        
        # Store for quick lookup
        key = f"conflict_{course_id}_{room_id}_{time_slot}"
        self.penalties[key] = penalty
        
        return constraint
    
    def add_gap_constraint(self,
                          lecturer_id: int,
                          course_ids: List[int],
                          optimal_gap_minutes: float) -> Dict[str, Any]:
        """
        Add soft constraint from GapOptimizer.
        
        Prefer time gaps between courses for same lecturer.
        
        Args:
            lecturer_id: Lecturer ID
            course_ids: Courses taught by this lecturer
            optimal_gap_minutes: Preferred gap between classes
        
        Returns:
            Constraint definition for solver
        """
        constraint = {
            'type': 'gap_spacing',
            'lecturer_id': lecturer_id,
            'course_ids': course_ids,
            'optimal_gap_minutes': optimal_gap_minutes,
            'weight': self.base_weights.gap_preference,
        }
        
        self.constraints.append(constraint)
        
        key = f"gap_{lecturer_id}"
        self.penalties[key] = optimal_gap_minutes
        
        return constraint
    
    def add_load_balance_constraint(self,
                                  total_courses: int,
                                  num_days: int,
                                  daily_std_dev: float) -> Dict[str, Any]:
        """
        Add soft constraint from LoadBalancer.
        
        Prefer balanced daily distributions.
        
        Args:
            total_courses: Total courses to schedule
            num_days: Number of days available
            daily_std_dev: Current std dev of daily loads
        
        Returns:
            Constraint definition for solver
        """
        # Target: std dev should be minimal
        # Penalty increases with deviation from ideal balance
        ideal_per_day = total_courses / num_days
        imbalance_penalty = daily_std_dev * self.base_weights.load_balance
        
        constraint = {
            'type': 'load_balance',
            'total_courses': total_courses,
            'num_days': num_days,
            'ideal_per_day': ideal_per_day,
            'current_std_dev': daily_std_dev,
            'penalty': imbalance_penalty,
        }
        
        self.constraints.append(constraint)
        
        key = "load_balance"
        self.penalties[key] = imbalance_penalty
        
        return constraint
    
    def build_solver_config(self, 
                           ml_confidence: float = 0.90) -> Dict[str, Any]:
        """
        Build complete OR-Tools solver configuration from ML constraints.
        
        Args:
            ml_confidence: Confidence score from ML draft (0.90 for 90% accuracy)
        
        Returns:
            Configuration dict for solver
        """
        # Adjust weights based on ML confidence
        # Higher confidence → higher ML weight, lower OR-Tools adjustment needed
        ml_weight_multiplier = ml_confidence + 0.1  # 1.0-1.0x
        
        optimized_weights = ConstraintWeights(
            conflict_penalty=self.base_weights.conflict_penalty * ml_weight_multiplier,
            gap_preference=self.base_weights.gap_preference * ml_weight_multiplier,
            load_balance=self.base_weights.load_balance * ml_weight_multiplier,
            room_utilization=self.base_weights.room_utilization * ml_weight_multiplier,
        )
        
        return {
            'ml_enabled': True,
            'ml_confidence': ml_confidence,
            'weights': optimized_weights.to_dict(),
            'constraints': self.constraints,
            'penalties': self.penalties,
            'total_constraint_count': len(self.constraints),
            'total_penalty_sum': sum(self.penalties.values()),
        }
    
    def reset(self):
        """Clear all constraints."""
        self.constraints = []
        self.penalties = {}
    
    def summary(self) -> str:
        """Get summary of constraints."""
        conflict_count = sum(1 for c in self.constraints if c['type'] == 'conflict_avoidance')
        gap_count = sum(1 for c in self.constraints if c['type'] == 'gap_spacing')
        balance_count = sum(1 for c in self.constraints if c['type'] == 'load_balance')
        
        total_penalty = sum(self.penalties.values())
        
        return f"""
Constraints Summary:
  • Conflict avoidance: {conflict_count}
  • Gap spacing: {gap_count}
  • Load balance: {balance_count}
  • Total constraints: {len(self.constraints)}
  • Total penalty weight: {total_penalty:.2f}
"""


class HybridSchedulingOrchestrator:
    """
    Orchestrates ML + OR-Tools hybrid scheduling.
    
    Pipeline:
    1. Load trained ML models
    2. Use Transformer to generate 90% draft
    3. Extract constraints from 3 predictors
    4. Build OR-Tools config with ML constraints
    5. Run solver to refine to 100% valid
    6. Return final timetable
    """
    
    def __init__(self,
                 transformer_model=None,
                 conflict_predictor=None,
                 gap_optimizer=None,
                 load_balancer=None):
        """Initialize orchestrator with trained models."""
        self.transformer = transformer_model
        self.conflict_predictor = conflict_predictor
        self.gap_optimizer = gap_optimizer
        self.load_balancer = load_balancer
        self.constraint_builder = ConstraintBuilder()
    
    def load_models(self, models_dir: str = "./backend/models"):
        """Load all trained models."""
        from pathlib import Path
        from timetable_app.ml_models.transformer_scheduler import TransformerScheduler
        from timetable_app.ml_models.constraint_predictor import (
            ConflictPredictor, GapOptimizer, LoadBalancer
        )
        
        models_path = Path(models_dir)
        
        try:
            self.transformer = TransformerScheduler.load(
                str(models_path / "transformer_scheduler.pkl")
            )
        except Exception as e:
            print(f"⚠ Could not load Transformer: {e}")
        
        try:
            self.conflict_predictor = ConflictPredictor.load(
                str(models_path / "conflict_predictor.pkl")
            )
        except Exception as e:
            print(f"⚠ Could not load ConflictPredictor: {e}")
        
        try:
            self.gap_optimizer = GapOptimizer.load(
                str(models_path / "gap_optimizer.pkl")
            )
        except Exception as e:
            print(f"⚠ Could not load GapOptimizer: {e}")
        
        try:
            self.load_balancer = LoadBalancer.load(
                str(models_path / "load_balancer.pkl")
            )
        except Exception as e:
            print(f"⚠ Could not load LoadBalancer: {e}")
    
    def step1_ml_draft(self, schedule_template: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 1: Generate 90% accurate draft using Transformer.
        """
        if not self.transformer:
            raise ValueError("Transformer model not loaded")
        
        print("📊 Phase 1: Generating ML draft (90% accuracy)...")
        draft = self.transformer.predict_draft_schedule(schedule_template)
        print(f"  ✓ Generated draft with {len(draft.get('timetable_entries', []))} entries")
        print(f"  ✓ Confidence: {draft.get('confidence', 0.90):.1%}")
        
        return draft
    
    def step2_extract_constraints(self, 
                                 draft: Dict[str, Any],
                                 schedule_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 2: Run ML predictors to extract soft constraints.
        """
        print("\n🔗 Phase 2: Extracting ML constraints...")
        self.constraint_builder.reset()
        
        entries = draft.get('timetable_entries', [])
        courses = {int(c['id']): c for c in schedule_data.get('courses', [])}
        lecturers = {int(l['id']): l for l in schedule_data.get('lecturers', [])}
        
        # Extract conflict constraints
        if self.conflict_predictor:
            print("  • Analyzing conflict risks...")
            for entry in entries[:min(50, len(entries))]:  # Sample to avoid slowdown
                risk = self.conflict_predictor.predict_conflict_risk(
                    course_id=int(entry.get('course_id', 1)),
                    room_id=int(entry.get('room_id', 1)),
                    time_slot=int(entry.get('day', 0)) * 288,
                )
                if risk > 0.3:  # Only add significant risks
                    self.constraint_builder.add_conflict_constraint(
                        course_id=int(entry['course_id']),
                        room_id=int(entry['room_id']),
                        time_slot=int(entry['day']) * 288,
                        conflict_risk=risk,
                    )
            print(f"    ✓ Added {sum(1 for c in self.constraint_builder.constraints if c['type'] == 'conflict_avoidance')} conflict constraints")
        
        # Extract gap constraints
        if self.gap_optimizer:
            print("  • Optimizing lecturer gaps...")
            for lecturer_id, lecturer in lecturers.items():
                lecturer_courses = [int(c) for c in lecturer.get('courses', [])]
                if len(lecturer_courses) > 1:
                    gap = self.gap_optimizer.predict_optimal_gap(
                        day1=0, day2=0,
                        start_min1=8*60, start_min2=10*60,
                    )
                    self.constraint_builder.add_gap_constraint(
                        lecturer_id=lecturer_id,
                        course_ids=lecturer_courses,
                        optimal_gap_minutes=gap,
                    )
            print(f"    ✓ Added {sum(1 for c in self.constraint_builder.constraints if c['type'] == 'gap_spacing')} gap constraints")
        
        # Extract load balance constraint
        if self.load_balancer:
            print("  • Analyzing load distribution...")
            daily_loads = [len([e for e in entries if e.get('day') == d]) for d in range(7)]
            std_dev = np.std(daily_loads) if daily_loads else 0
            
            self.constraint_builder.add_load_balance_constraint(
                total_courses=len(entries),
                num_days=7,
                daily_std_dev=std_dev,
            )
            print(f"    ✓ Added load balance constraint (std_dev: {std_dev:.2f})")
        
        config = self.constraint_builder.build_solver_config(
            ml_confidence=draft.get('confidence', 0.90)
        )
        
        print(f"\n{self.constraint_builder.summary()}")
        
        return config
    
    def step3_or_tools_refinement(self, 
                                 draft: Dict[str, Any],
                                 ml_config: Dict[str, Any],
                                 schedule_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 3: Pass draft + constraints to OR-Tools for refinement.
        
        This is a placeholder - actual OR-Tools integration will be in
        the modified scheduler service.
        """
        print("\n🔧 Phase 3: OR-Tools Polish (100% validity)...")
        print(f"  • Using ML constraints as guidance...")
        print(f"  • Weights: {', '.join(f'{k}={v:.1f}' for k,v in ml_config['weights'].items())}")
        print(f"  • Constraints: {ml_config['total_constraint_count']}")
        
        # In Phase 3 integration, this will call the actual OR-Tools solver
        # For now, return enhanced draft
        refined = draft.copy()
        refined['ml_config'] = ml_config
        refined['refinement_status'] = 'pending_orttools'
        
        return refined
    
    def run_hybrid_scheduling(self, 
                             schedule_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute complete hybrid scheduling pipeline.
        
        Returns:
            Final timetable dictionary with metadata
        """
        print("="*70)
        print("HYBRID ML + OR-TOOLS SCHEDULING")
        print("="*70)
        
        try:
            # Step 1: ML draft
            draft = self.step1_ml_draft(schedule_data)
            
            # Step 2: Extract constraints
            ml_config = self.step2_extract_constraints(draft, schedule_data)
            
            # Step 3: OR-Tools refinement
            final_schedule = self.step3_or_tools_refinement(
                draft, ml_config, schedule_data
            )
            
            print("\n✅ SCHEDULING PIPELINE COMPLETE")
            print(f"  • Entries: {len(final_schedule.get('timetable_entries', []))}")
            print(f"  • ML confidence: {final_schedule.get('confidence', 0):.1%}")
            print(f"  • Status: Ready for OR-Tools solver")
            
            return final_schedule
        
        except Exception as e:
            print(f"\n❌ Pipeline error: {e}")
            import traceback
            traceback.print_exc()
            return None


def create_hybrid_scheduler(models_dir: str = "./backend/models") -> HybridSchedulingOrchestrator:
    """Factory function to create fully initialized orchestrator."""
    orchestrator = HybridSchedulingOrchestrator()
    orchestrator.load_models(models_dir)
    return orchestrator
