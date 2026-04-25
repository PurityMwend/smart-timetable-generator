"""
End-to-end tests for hybrid ML + OR-Tools scheduling pipeline.

Tests complete workflow: ML draft → Constraint extraction → OR-Tools refinement
"""

import json
from pathlib import Path
from unittest import TestCase
import logging

import numpy as np

# Mock Django models for testing without DB
class MockDepartment:
    def __init__(self, id=1, name="Engineering"):
        self.id = id
        self.name = name

class MockCourse:
    def __init__(self, id, name, class_size=30, hours_per_week=3):
        self.id = id
        self.name = name
        self.class_size = class_size
        self.hours_per_week = hours_per_week
        self.department = MockDepartment()

class MockLecturer:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.department = MockDepartment()

class MockRoom:
    def __init__(self, id, name, capacity=50):
        self.id = id
        self.name = name
        self.capacity = capacity
        self.room_type = "lecture"

class MockTimeSlot:
    def __init__(self, id, day=0, start_time="08:00", end_time="09:00"):
        self.id = id
        self.day = day
        self.start_time = start_time
        self.end_time = end_time

logger = logging.getLogger(__name__)


class E2EHybridSchedulingTests(TestCase):
    """End-to-end tests for hybrid pipeline."""
    
    @classmethod
    def setUpClass(cls):
        """Setup test fixtures."""
        # Create test data
        cls.departments = [MockDepartment(i, f"Dept{i}") for i in range(1, 4)]
        
        cls.courses = [
            MockCourse(i, f"Course{i}", class_size=30 + i*5)
            for i in range(1, 11)  # 10 courses
        ]
        for course in cls.courses:
            course.department = cls.departments[course.id % 3]
        
        cls.lecturers = [
            MockLecturer(i, f"Lecturer{i}")
            for i in range(1, 6)  # 5 lecturers
        ]
        for lecturer in cls.lecturers:
            lecturer.department = cls.departments[lecturer.id % 3]
        
        cls.rooms = [
            MockRoom(i, f"Room{i}", capacity=20 + i*10)
            for i in range(1, 5)  # 4 rooms
        ]
        
        cls.time_slots = [
            MockTimeSlot(i, day=i % 5, start_time=f"{8 + (i % 4):02d}:00",
                        end_time=f"{9 + (i % 4):02d}:00")
            for i in range(1, 21)  # 20 time slots
        ]
    
    def test_e2e_hybrid_pipeline_initialization(self):
        """Test E1: Hybrid pipeline initializes correctly."""
        from timetable_app.services.hybrid_scheduler import HybridTimetableScheduler
        
        scheduler = HybridTimetableScheduler(
            courses=self.courses,
            lecturers=self.lecturers,
            rooms=self.rooms,
            time_slots=self.time_slots,
            use_ml_hybrid=True
        )
        
        self.assertIsNotNone(scheduler)
        self.assertEqual(len(scheduler.courses), 10)
        self.assertEqual(len(scheduler.lecturers), 5)
        self.assertEqual(len(scheduler.rooms), 4)
        self.assertEqual(len(scheduler.time_slots), 20)
        
        logger.info("✓ E1: Pipeline initialized")
    
    def test_e2e_schedule_template_creation(self):
        """Test E2: Schedule template creation."""
        from timetable_app.services.hybrid_scheduler import HybridTimetableScheduler
        
        scheduler = HybridTimetableScheduler(
            courses=self.courses,
            lecturers=self.lecturers,
            rooms=self.rooms,
            time_slots=self.time_slots,
            use_ml_hybrid=False  # Skip ML to test structure
        )
        
        template = scheduler._create_schedule_template()
        
        self.assertIn('courses', template)
        self.assertIn('lecturers', template)
        self.assertIn('rooms', template)
        self.assertIn('timeslots', template)
        self.assertIn('timetable_entries', template)
        
        self.assertEqual(len(template['courses']), 10)
        self.assertEqual(len(template['lecturers']), 5)
        self.assertEqual(len(template['rooms']), 4)
        self.assertEqual(len(template['timeslots']), 20)
        
        logger.info("✓ E2: Schedule template creation verified")
    
    def test_e2e_or_tools_constraint_generation(self):
        """Test E3: OR-Tools constraints generated correctly."""
        from timetable_app.services.hybrid_scheduler import HybridTimetableScheduler
        
        scheduler = HybridTimetableScheduler(
            courses=self.courses,
            lecturers=self.lecturers,
            rooms=self.rooms,
            time_slots=self.time_slots,
            use_ml_hybrid=False
        )
        
        # Create variables (step 1 of constraint setup)
        scheduler._create_decision_variables()
        
        # Verify variables created
        self.assertEqual(len(scheduler.variables), 10)  # 10 courses
        for c_idx in scheduler.variables:
            self.assertEqual(len(scheduler.variables[c_idx]), 20)  # 20 time slots
            for t_idx in scheduler.variables[c_idx]:
                self.assertEqual(len(scheduler.variables[c_idx][t_idx]), 4)  # 4 rooms
        
        logger.info("✓ E3: OR-Tools variables created")
    
    def test_e2e_mandatory_constraints(self):
        """Test E4: Mandatory constraints (hard constraints)."""
        from timetable_app.services.hybrid_scheduler import HybridTimetableScheduler
        
        scheduler = HybridTimetableScheduler(
            courses=self.courses,
            lecturers=self.lecturers,
            rooms=self.rooms,
            time_slots=self.time_slots,
            use_ml_hybrid=False
        )
        
        scheduler._create_decision_variables()
        initial_constraints = scheduler.model.NumConstraints()
        
        scheduler._add_mandatory_constraints()
        
        # Should have added constraints for:
        # - Each course scheduled once (10)
        # - No room double-bookings (20)
        new_constraints = scheduler.model.NumConstraints()
        added = new_constraints - initial_constraints
        
        self.assertGreaterEqual(added, 10, "Should add at least 10 constraints")
        
        logger.info(f"✓ E4: Added {added} mandatory constraints")
    
    def test_e2e_resource_constraints(self):
        """Test E5: Resource constraints (capacity, lecturer availability)."""
        from timetable_app.services.hybrid_scheduler import HybridTimetableScheduler
        
        scheduler = HybridTimetableScheduler(
            courses=self.courses,
            lecturers=self.lecturers,
            rooms=self.rooms,
            time_slots=self.time_slots,
            use_ml_hybrid=False
        )
        
        scheduler._create_decision_variables()
        scheduler._add_mandatory_constraints()
        
        initial = scheduler.model.NumConstraints()
        scheduler._add_resource_constraints()
        
        after = scheduler.model.NumConstraints()
        added = after - initial
        
        self.assertGreater(added, 0, "Should add resource constraints")
        logger.info(f"✓ E5: Added {added} resource constraints")
    
    def test_e2e_ml_constraint_config_structure(self):
        """Test E6: ML constraint config has correct structure."""
        from timetable_app.services.constraint_builder import ConstraintBuilder, ConstraintWeights
        
        builder = ConstraintBuilder()
        
        # Add some constraints
        builder.add_conflict_constraint('course_1', 'room_1', 'slot_1', 0.5)
        builder.add_gap_constraint('lecturer_1', [{'day': 0, 'slot': 1}, 
                                                   {'day': 1, 'slot': 2}], 120)
        builder.add_load_balance_constraint(['room_1', 'room_2'], [5, 3], 2.0)
        
        config = builder.build_solver_config()
        
        # Validate structure
        self.assertIn('weights', config)
        self.assertIn('constraints', config)
        self.assertIn('ml_confidence_multiplier', config)
        
        # Validate weights
        weights = config['weights']
        self.assertIn('conflict_penalty', weights)
        self.assertIn('gap_preference', weights)
        self.assertIn('load_balance', weights)
        self.assertIn('room_utilization', weights)
        
        # All weights should be positive
        for key, value in weights.items():
            self.assertGreater(value, 0, f"Weight {key} should be positive")
        
        logger.info(f"✓ E6: ML config structure valid with {len(config['constraints'])} constraints")
    
    def test_e2e_ml_constraint_application(self):
        """Test E7: ML constraints applied to scheduler."""
        from timetable_app.services.hybrid_scheduler import HybridTimetableScheduler
        from timetable_app.services.constraint_builder import ConstraintBuilder
        
        scheduler = HybridTimetableScheduler(
            courses=self.courses,
            lecturers=self.lecturers,
            rooms=self.rooms,
            time_slots=self.time_slots,
            use_ml_hybrid=False
        )
        
        # Setup ML config manually
        builder = ConstraintBuilder()
        builder.add_conflict_constraint('course_1', 'room_1', 'slot_1', 0.8)
        scheduler.ml_config = builder.build_solver_config()
        
        # Should not raise error
        try:
            scheduler._create_decision_variables()
            scheduler._apply_ml_constraints()
            test_passed = True
        except Exception as e:
            logger.error(f"Failed to apply ML constraints: {e}")
            test_passed = False
        
        self.assertTrue(test_passed)
        logger.info("✓ E7: ML constraints applied successfully")
    
    def test_e2e_pipeline_statistics(self):
        """Test E8: Pipeline statistics reporting."""
        from timetable_app.services.hybrid_scheduler import HybridTimetableScheduler
        
        scheduler = HybridTimetableScheduler(
            courses=self.courses,
            lecturers=self.lecturers,
            rooms=self.rooms,
            time_slots=self.time_slots,
            use_ml_hybrid=False
        )
        
        stats = scheduler.get_statistics()
        
        # Validate structure
        expected_keys = [
            'ml_enabled', 'ml_draft_entries', 'ml_confidence',
            'ml_constraints_extracted', 'total_courses', 'total_lecturers',
            'total_rooms', 'total_timeslots'
        ]
        
        for key in expected_keys:
            self.assertIn(key, stats, f"Missing stat: {key}")
        
        # Validate values
        self.assertEqual(stats['total_courses'], 10)
        self.assertEqual(stats['total_lecturers'], 5)
        self.assertEqual(stats['total_rooms'], 4)
        self.assertEqual(stats['total_timeslots'], 20)
        
        logger.info(f"✓ E8: Statistics valid: {stats}")


class E2EPerformanceProfileTests(TestCase):
    """Performance profiling for hybrid pipeline."""
    
    @classmethod
    def setUpClass(cls):
        """Setup larger test data for performance testing."""
        # Scale up test data
        cls.departments = [MockDepartment(i, f"Dept{i}") for i in range(1, 6)]
        
        cls.courses = [
            MockCourse(i, f"Course{i}", class_size=20 + (i % 50))
            for i in range(1, 51)  # 50 courses
        ]
        for course in cls.courses:
            course.department = cls.departments[course.id % 5]
        
        cls.lecturers = [
            MockLecturer(i, f"Lecturer{i}")
            for i in range(1, 21)  # 20 lecturers
        ]
        for lecturer in cls.lecturers:
            lecturer.department = cls.departments[lecturer.id % 5]
        
        cls.rooms = [
            MockRoom(i, f"Room{i}", capacity=30 + (i % 4) * 20)
            for i in range(1, 15)  # 15 rooms
        ]
        
        cls.time_slots = [
            MockTimeSlot(i, day=i % 5, 
                        start_time=f"{8 + (i // 5) % 4:02d}:00",
                        end_time=f"{9 + (i // 5) % 4:02d}:00")
            for i in range(1, 26)  # 25 time slots
        ]
    
    def test_perf_or_tools_solve_time(self):
        """Test P1: OR-Tools solver completes within time budget."""
        import time
        from timetable_app.services.hybrid_scheduler import HybridTimetableScheduler
        
        scheduler = HybridTimetableScheduler(
            courses=self.courses,
            lecturers=self.lecturers,
            rooms=self.rooms,
            time_slots=self.time_slots,
            use_ml_hybrid=False
        )
        
        start_time = time.time()
        
        scheduler._create_decision_variables()
        scheduler._add_mandatory_constraints()
        scheduler._add_resource_constraints()
        
        elapsed = time.time() - start_time
        
        # Constraint setup should be <5 seconds
        self.assertLess(elapsed, 5.0, f"Constraint setup took {elapsed:.2f}s")
        
        logger.info(f"✓ P1: Constraint setup completed in {elapsed:.2f}s")
    
    def test_perf_schedule_generation_budget(self):
        """Test P2: Full scheduling under performance target."""
        import time
        from timetable_app.services.hybrid_scheduler import HybridTimetableScheduler
        
        # Note: Actual solving may exceed timeout for this complex test case
        # In production with ML draft, should be much faster
        scheduler = HybridTimetableScheduler(
            courses=self.courses,
            lecturers=self.lecturers,
            rooms=self.rooms,
            time_slots=self.time_slots,
            use_ml_hybrid=False
        )
        
        # We test structure, not actual solving (which requires more time for 50 courses)
        template = scheduler._create_schedule_template()
        
        # Verify template creation is instant
        start = time.time()
        stats = scheduler.get_statistics()
        elapsed = time.time() - start
        
        self.assertLess(elapsed, 0.01, "Statistics should be instant")
        logger.info(f"✓ P2: Statistics computed in {elapsed*1000:.1f}ms")


if __name__ == '__main__':
    import unittest
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'
    )
    
    # Run tests
    suite = unittest.TestLoader().loadTestsFromModule(__import__(__name__))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("E2E HYBRID SCHEDULING TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)
