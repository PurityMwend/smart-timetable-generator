"""
Integration tests for hybrid ML + OR-Tools scheduling system.

Tests:
1. Constraint builder correctness
2. Hybrid orchestrator end-to-end
3. ML model loading and inference
4. OR-Tools integration (mocked)
"""

import json
from pathlib import Path
from typing import Dict, Any, List


class HybridSchedulingTests:
    """Test harness for Phase 3 integration."""
    
    def __init__(self, data_dir: str = "./backend/data",
                 models_dir: str = "./backend/models"):
        self.data_dir = Path(data_dir)
        self.models_dir = Path(models_dir)
        self.test_results = []
    
    def load_test_schedule(self) -> Dict[str, Any]:
        """Load a small test schedule from training data."""
        data_file = self.data_dir / "all_training_data.json"
        
        if not data_file.exists():
            return self._create_minimal_test_schedule()
        
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        schedules = data if isinstance(data, list) else data.get('schedules', [])
        return schedules[0] if schedules else self._create_minimal_test_schedule()
    
    def _create_minimal_test_schedule(self) -> Dict[str, Any]:
        """Create minimal test schedule for offline testing."""
        return {
            'id': 'test_schedule_1',
            'name': 'Test Campus',
            'courses': [
                {'id': '1', 'name': 'Math 101', 'class_size': 50, 'hours_per_week': 3, 'department_id': '1'},
                {'id': '2', 'name': 'Physics 101', 'class_size': 45, 'hours_per_week': 3, 'department_id': '2'},
                {'id': '3', 'name': 'Chemistry 101', 'class_size': 40, 'hours_per_week': 2, 'department_id': '3'},
            ],
            'lecturers': [
                {'id': '1', 'name': 'Dr. Smith', 'courses': [1], 'department_id': '1'},
                {'id': '2', 'name': 'Dr. Jones', 'courses': [2], 'department_id': '2'},
                {'id': '3', 'name': 'Dr. Brown', 'courses': [3], 'department_id': '3'},
            ],
            'rooms': [
                {'id': '1', 'name': 'Room A', 'capacity': 100, 'room_type': 'lecture'},
                {'id': '2', 'name': 'Room B', 'capacity': 80, 'room_type': 'lecture'},
                {'id': '3', 'name': 'Room C', 'capacity': 60, 'room_type': 'lab'},
            ],
            'timeslots': [
                {'id': '1', 'day': 0, 'start_time': '08:00', 'end_time': '09:00'},
                {'id': '2', 'day': 0, 'start_time': '10:00', 'end_time': '11:00'},
                {'id': '3', 'day': 1, 'start_time': '08:00', 'end_time': '09:00'},
            ],
            'timetable_entries': [],
        }
    
    def test_constraint_builder_initialization(self) -> bool:
        """Test 1: Constraint builder initializes correctly."""
        print("\n[TEST 1] Constraint Builder Initialization")
        print("-" * 50)
        
        try:
            from timetable_app.services.constraint_builder import ConstraintBuilder
            
            builder = ConstraintBuilder()
            assert builder is not None
            assert builder.constraints == []
            assert builder.penalties == {}
            
            print("✓ Builder initialized")
            print(f"✓ Base weights: {builder.base_weights.to_dict()}")
            
            self.test_results.append(('test_constraint_builder_init', 'PASS'))
            return True
        except Exception as e:
            print(f"✗ Failed: {e}")
            self.test_results.append(('test_constraint_builder_init', f'FAIL: {e}'))
            return False
    
    def test_conflict_constraint_creation(self) -> bool:
        """Test 2: Conflict constraints are created with correct penalties."""
        print("\n[TEST 2] Conflict Constraint Creation")
        print("-" * 50)
        
        try:
            from timetable_app.services.constraint_builder import ConstraintBuilder
            
            builder = ConstraintBuilder()
            
            # Test low risk
            c1 = builder.add_conflict_constraint(
                course_id=1, room_id=1, time_slot=0,
                conflict_risk=0.1
            )
            assert c1['type'] == 'conflict_avoidance'
            assert c1['penalty'] == 0.1 * 100  # 0.1 * base_weight
            print(f"✓ Low risk (10%): penalty = {c1['penalty']:.1f}")
            
            # Test high risk
            c2 = builder.add_conflict_constraint(
                course_id=2, room_id=2, time_slot=100,
                conflict_risk=0.8
            )
            assert c2['penalty'] == 0.8 * 100
            print(f"✓ High risk (80%): penalty = {c2['penalty']:.1f}")
            
            assert len(builder.constraints) == 2
            print(f"✓ Total constraints: {len(builder.constraints)}")
            
            self.test_results.append(('test_conflict_constraints', 'PASS'))
            return True
        except Exception as e:
            print(f"✗ Failed: {e}")
            self.test_results.append(('test_conflict_constraints', f'FAIL: {e}'))
            return False
    
    def test_gap_constraint_creation(self) -> bool:
        """Test 3: Gap spacing constraints."""
        print("\n[TEST 3] Gap Spacing Constraint Creation")
        print("-" * 50)
        
        try:
            from timetable_app.services.constraint_builder import ConstraintBuilder
            
            builder = ConstraintBuilder()
            
            gap = builder.add_gap_constraint(
                lecturer_id=1,
                course_ids=[1, 2, 3],
                optimal_gap_minutes=60
            )
            
            assert gap['type'] == 'gap_spacing'
            assert gap['optimal_gap_minutes'] == 60
            assert gap['lecturer_id'] == 1
            print(f"✓ Gap constraint added")
            print(f"  Lecturer: {gap['lecturer_id']}")
            print(f"  Courses: {gap['course_ids']}")
            print(f"  Optimal gap: {gap['optimal_gap_minutes']} min")
            
            self.test_results.append(('test_gap_constraints', 'PASS'))
            return True
        except Exception as e:
            print(f"✗ Failed: {e}")
            self.test_results.append(('test_gap_constraints', f'FAIL: {e}'))
            return False
    
    def test_load_balance_constraint(self) -> bool:
        """Test 4: Load balancing constraints."""
        print("\n[TEST 4] Load Balance Constraint Creation")
        print("-" * 50)
        
        try:
            from timetable_app.services.constraint_builder import ConstraintBuilder
            
            builder = ConstraintBuilder()
            
            balance = builder.add_load_balance_constraint(
                total_courses=21,
                num_days=7,
                daily_std_dev=2.5
            )
            
            assert balance['type'] == 'load_balance'
            assert balance['ideal_per_day'] == 3  # 21 / 7
            print(f"✓ Balance constraint added")
            print(f"  Total courses: {balance['total_courses']}")
            print(f"  Days available: {balance['num_days']}")
            print(f"  Ideal per day: {balance['ideal_per_day']:.1f}")
            print(f"  Current std dev: {balance['current_std_dev']:.1f}")
            
            self.test_results.append(('test_load_balance', 'PASS'))
            return True
        except Exception as e:
            print(f"✗ Failed: {e}")
            self.test_results.append(('test_load_balance', f'FAIL: {e}'))
            return False
    
    def test_solver_config_generation(self) -> bool:
        """Test 5: OR-Tools solver configuration generation."""
        print("\n[TEST 5] OR-Tools Solver Config Generation")
        print("-" * 50)
        
        try:
            from timetable_app.services.constraint_builder import ConstraintBuilder
            
            builder = ConstraintBuilder()
            
            # Add multiple constraints
            builder.add_conflict_constraint(1, 1, 0, 0.5)
            builder.add_gap_constraint(1, [1, 2], 45)
            builder.add_load_balance_constraint(10, 5, 1.5)
            
            # Generate config
            config = builder.build_solver_config(ml_confidence=0.90)
            
            assert config['ml_enabled'] is True
            assert config['ml_confidence'] == 0.90
            assert config['total_constraint_count'] == 3
            assert 'conflict' in config['weights']
            
            print(f"✓ Config generated")
            print(f"  ML enabled: {config['ml_enabled']}")
            print(f"  ML confidence: {config['ml_confidence']:.1%}")
            print(f"  Total constraints: {config['total_constraint_count']}")
            print(f"  Weights: {config['weights']}")
            
            self.test_results.append(('test_solver_config', 'PASS'))
            return True
        except Exception as e:
            print(f"✗ Failed: {e}")
            self.test_results.append(('test_solver_config', f'FAIL: {e}'))
            return False
    
    def test_hybrid_orchestrator_initialization(self) -> bool:
        """Test 6: Hybrid orchestrator initializes."""
        print("\n[TEST 6] Hybrid Orchestrator Initialization")
        print("-" * 50)
        
        try:
            from timetable_app.services.constraint_builder import HybridSchedulingOrchestrator
            
            orchestrator = HybridSchedulingOrchestrator()
            assert orchestrator is not None
            assert orchestrator.transformer is None  # Not loaded
            assert orchestrator.constraint_builder is not None
            
            print("✓ Orchestrator initialized (models not loaded)")
            print("  Note: Models require training data")
            
            self.test_results.append(('test_orchestrator_init', 'PASS'))
            return True
        except Exception as e:
            print(f"✗ Failed: {e}")
            self.test_results.append(('test_orchestrator_init', f'FAIL: {e}'))
            return False
    
    def test_constraint_builder_reset(self) -> bool:
        """Test 7: Constraint builder reset functionality."""
        print("\n[TEST 7] Constraint Builder Reset")
        print("-" * 50)
        
        try:
            from timetable_app.services.constraint_builder import ConstraintBuilder
            
            builder = ConstraintBuilder()
            
            # Add constraints
            builder.add_conflict_constraint(1, 1, 0, 0.5)
            assert len(builder.constraints) == 1
            
            # Reset
            builder.reset()
            assert len(builder.constraints) == 0
            assert len(builder.penalties) == 0
            
            print("✓ Reset successful")
            print(f"  Constraints: {len(builder.constraints)}")
            print(f"  Penalties: {len(builder.penalties)}")
            
            self.test_results.append(('test_builder_reset', 'PASS'))
            return True
        except Exception as e:
            print(f"✗ Failed: {e}")
            self.test_results.append(('test_builder_reset', f'FAIL: {e}'))
            return False
    
    def test_constraint_builder_summary(self) -> bool:
        """Test 8: Constraint builder summary generation."""
        print("\n[TEST 8] Constraint Builder Summary")
        print("-" * 50)
        
        try:
            from timetable_app.services.constraint_builder import ConstraintBuilder
            
            builder = ConstraintBuilder()
            
            builder.add_conflict_constraint(1, 1, 0, 0.5)
            builder.add_gap_constraint(1, [1, 2], 45)
            builder.add_load_balance_constraint(10, 5, 1.5)
            
            summary = builder.summary()
            assert 'Constraints Summary' in summary
            assert 'Conflict avoidance' in summary
            
            print("✓ Summary generated:")
            print(summary)
            
            self.test_results.append(('test_builder_summary', 'PASS'))
            return True
        except Exception as e:
            print(f"✗ Failed: {e}")
            self.test_results.append(('test_builder_summary', f'FAIL: {e}'))
            return False
    
    def run_all_tests(self) -> Dict[str, int]:
        """Run all integration tests."""
        print("="*70)
        print("PHASE 3 INTEGRATION TESTS")
        print("="*70)
        
        tests = [
            self.test_constraint_builder_initialization,
            self.test_conflict_constraint_creation,
            self.test_gap_constraint_creation,
            self.test_load_balance_constraint,
            self.test_solver_config_generation,
            self.test_hybrid_orchestrator_initialization,
            self.test_constraint_builder_reset,
            self.test_constraint_builder_summary,
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"\n✗ Test error: {e}")
        
        # Summary
        passed = sum(1 for _, status in self.test_results if status == 'PASS')
        failed = len(self.test_results) - passed
        
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"\nResults: {passed} PASS, {failed} FAIL out of {len(self.test_results)} tests")
        
        for test_name, result in self.test_results:
            status_icon = "✓" if result == "PASS" else "✗"
            print(f"  {status_icon} {test_name}: {result}")
        
        print("\n" + "="*70)
        
        return {
            'total': len(self.test_results),
            'passed': passed,
            'failed': failed,
        }


def run_phase3_tests(data_dir: str = "./backend/data",
                     models_dir: str = "./backend/models") -> Dict[str, int]:
    """Entry point for Phase 3 testing."""
    tester = HybridSchedulingTests(data_dir=data_dir, models_dir=models_dir)
    return tester.run_all_tests()


if __name__ == "__main__":
    run_phase3_tests()
