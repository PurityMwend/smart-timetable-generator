"""
Success Metrics Validator for Hybrid ML + OR-Tools Timetable Generator.

Validates all 4 success metrics:
1. Zero Hard Conflicts (100% weight, critical)
2. Gap Minimization > 0.8 (50% weight, high)
3. Distribution < 20% variance (30% weight, medium)
4. < 2 minutes execution (20% weight, low)
"""

import time
import json
from typing import Dict, List, Any, Tuple
from pathlib import Path
from collections import defaultdict
import statistics
import logging

logger = logging.getLogger(__name__)


class MetricsValidator:
    """Validates timetable against success metrics."""
    
    def __init__(self):
        self.metrics = {
            'hard_conflicts': {'target': 0, 'weight': 100, 'actual': None, 'passed': False},
            'gap_minimization': {'target': 0.8, 'weight': 50, 'actual': None, 'passed': False},
            'distribution': {'target': 0.20, 'weight': 30, 'actual': None, 'passed': False},
            'execution_time': {'target': 120, 'weight': 20, 'actual': None, 'passed': False},
        }
        self.timetable_entries = []
        self.validation_summary = {}
    
    def validate_hard_conflicts(self, timetable_entries: List[Any]) -> Tuple[int, bool]:
        """
        Metric 1: Zero Hard Constraints (Critical)
        
        Hard conflicts are:
        - Room double-bookings (same room, same time)
        - Lecturer double-bookings (same lecturer, same time)
        - Room capacity violations (class size > room capacity)
        
        Args:
            timetable_entries: List of TimetableEntry objects
        
        Returns:
            (conflict_count, passed)
        """
        logger.info("Validating Metric 1: Hard Constraints (Zero Conflicts)")
        
        conflicts = 0
        room_schedule = defaultdict(list)  # room_id -> [(time_slot_id, course_id), ...]
        lecturer_schedule = defaultdict(list)  # lecturer_id -> [(time_slot_id, course_id), ...]
        
        for entry in timetable_entries:
            # Check room capacity
            if hasattr(entry, 'course') and hasattr(entry, 'room'):
                if entry.room.capacity < entry.course.class_size:
                    conflicts += 1
                    logger.warning(
                        f"  ✗ Capacity violation: {entry.course.name} ({entry.course.class_size} students) "
                        f"in {entry.room.name} (capacity {entry.room.capacity})"
                    )
            
            # Track room bookings
            room_key = (
                entry.room.id if hasattr(entry, 'room') else None,
                entry.time_slot.id if hasattr(entry, 'time_slot') else None
            )
            room_schedule[room_key].append(entry.course.id if hasattr(entry, 'course') else None)
            
            # Track lecturer bookings
            lecturer_key = (
                entry.lecturer.id if hasattr(entry, 'lecturer') else None,
                entry.time_slot.id if hasattr(entry, 'time_slot') else None
            )
            lecturer_schedule[lecturer_key].append(entry.course.id if hasattr(entry, 'course') else None)
        
        # Check room double-bookings
        for (room_id, slot_id), courses in room_schedule.items():
            if len(courses) > 1:
                conflicts += 1
                logger.warning(f"  ✗ Room {room_id} double-booked at slot {slot_id}: {len(courses)} courses")
        
        # Check lecturer double-bookings
        for (lecturer_id, slot_id), courses in lecturer_schedule.items():
            if len(courses) > 1:
                conflicts += 1
                logger.warning(f"  ✗ Lecturer {lecturer_id} double-booked at slot {slot_id}: {len(courses)} courses")
        
        passed = conflicts == 0
        self.metrics['hard_conflicts']['actual'] = conflicts
        self.metrics['hard_conflicts']['passed'] = passed
        
        if passed:
            logger.info(f"  ✓ PASSED: Zero conflicts detected ({len(timetable_entries)} valid entries)")
        else:
            logger.error(f"  ✗ FAILED: {conflicts} conflicts detected")
        
        return conflicts, passed
    
    def validate_gap_minimization(self, timetable_entries: List[Any]) -> Tuple[float, bool]:
        """
        Metric 2: Gap Minimization > 0.8 (High Priority)
        
        Measures how well lecturers' courses are clustered without long gaps.
        Score = 1.0 - (avg_gap_minutes / max_possible_gap)
        
        Goal: Score > 0.8 means gaps are minimized (avg gap < 20% of available time)
        
        Args:
            timetable_entries: List of TimetableEntry objects
        
        Returns:
            (gap_score, passed)
        """
        logger.info("Validating Metric 2: Gap Minimization Score")
        
        # Group courses by lecturer and day
        lecturer_schedule = defaultdict(lambda: defaultdict(list))
        
        for entry in timetable_entries:
            if hasattr(entry, 'lecturer') and hasattr(entry, 'time_slot'):
                lecturer_id = entry.lecturer.id
                day = entry.time_slot.day if hasattr(entry.time_slot, 'day') else 0
                slot_idx = entry.time_slot.id
                
                lecturer_schedule[lecturer_id][day].append(slot_idx)
        
        # Calculate gaps for each lecturer
        all_gaps = []
        
        for lecturer_id, days in lecturer_schedule.items():
            for day, slots in days.items():
                slots = sorted(set(slots))  # Remove duplicates, sort
                
                if len(slots) > 1:
                    # Calculate gaps between consecutive courses
                    gaps = []
                    for i in range(len(slots) - 1):
                        gap = slots[i + 1] - slots[i]
                        gaps.append(gap)
                    
                    all_gaps.extend(gaps)
        
        # Calculate gap score
        if all_gaps:
            avg_gap = statistics.mean(all_gaps)
            max_gap = max(all_gaps) if all_gaps else 1
            
            # Normalize: 0 gap → 1.0, large gap → lower score
            # Using 10 slots as reference for "max possible gap"
            gap_score = max(0, 1.0 - (avg_gap / 10.0))
        else:
            gap_score = 1.0  # No gaps if courses are perfectly clustered
        
        passed = gap_score > 0.8
        self.metrics['gap_minimization']['actual'] = gap_score
        self.metrics['gap_minimization']['passed'] = passed
        
        logger.info(f"  Gap Score: {gap_score:.3f}")
        logger.info(f"  Average gap between courses: {statistics.mean(all_gaps):.2f} slots" if all_gaps else "  No gaps")
        
        if passed:
            logger.info(f"  ✓ PASSED: Gap score {gap_score:.3f} > 0.8 threshold")
        else:
            logger.warning(f"  ✗ FAILED: Gap score {gap_score:.3f} ≤ 0.8 threshold")
        
        return gap_score, passed
    
    def validate_distribution(self, timetable_entries: List[Any]) -> Tuple[float, bool]:
        """
        Metric 3: Load Distribution < 20% Variance (Medium Priority)
        
        Measures how evenly classes are distributed across rooms and time slots.
        Variance = std_dev(courses_per_room) / mean(courses_per_room)
        
        Goal: Variance < 0.20 means even distribution
        
        Args:
            timetable_entries: List of TimetableEntry objects
        
        Returns:
            (variance_score, passed)
        """
        logger.info("Validating Metric 3: Load Distribution")
        
        # Count courses per room
        room_loads = defaultdict(int)
        time_slot_loads = defaultdict(int)
        
        for entry in timetable_entries:
            if hasattr(entry, 'room'):
                room_loads[entry.room.id] += 1
            if hasattr(entry, 'time_slot'):
                time_slot_loads[entry.time_slot.id] += 1
        
        # Calculate variance for room loads
        if room_loads:
            room_load_values = list(room_loads.values())
            mean_load = statistics.mean(room_load_values)
            
            if mean_load > 0:
                variance = statistics.stdev(room_load_values) / mean_load if len(room_load_values) > 1 else 0
            else:
                variance = 0
        else:
            variance = 0
            mean_load = 0
        
        passed = variance < 0.20
        self.metrics['distribution']['actual'] = variance
        self.metrics['distribution']['passed'] = passed
        
        logger.info(f"  Load Variance: {variance:.3f}")
        logger.info(f"  Mean courses per room: {mean_load:.1f}")
        logger.info(f"  Room load distribution: min={min(room_load_values) if room_load_values else 0}, "
                   f"max={max(room_load_values) if room_load_values else 0}")
        
        if passed:
            logger.info(f"  ✓ PASSED: Variance {variance:.3f} < 0.20 threshold")
        else:
            logger.warning(f"  ✗ FAILED: Variance {variance:.3f} ≥ 0.20 threshold")
        
        return variance, passed
    
    def validate_execution_time(self, end_time: float, start_time: float) -> Tuple[float, bool]:
        """
        Metric 4: Execution Time < 2 minutes (Low Priority)
        
        Measures total time from ML draft to final timetable.
        
        Goal: < 120 seconds on typical hardware
        
        Args:
            end_time: End time (seconds)
            start_time: Start time (seconds)
        
        Returns:
            (elapsed_time, passed)
        """
        logger.info("Validating Metric 4: Execution Time")
        
        elapsed = end_time - start_time
        passed = elapsed < 120
        
        self.metrics['execution_time']['actual'] = elapsed
        self.metrics['execution_time']['passed'] = passed
        
        logger.info(f"  Execution Time: {elapsed:.2f} seconds")
        
        if passed:
            logger.info(f"  ✓ PASSED: {elapsed:.2f}s < 120s target")
        else:
            logger.warning(f"  ✗ FAILED: {elapsed:.2f}s ≥ 120s target")
        
        return elapsed, passed
    
    def calculate_weighted_score(self) -> float:
        """
        Calculate weighted success score.
        
        Score = (metric1_pass * 100 + metric2_actual * 50 + metric3_pass * 30 + metric4_pass * 20) / 200
        
        Returns:
            Score from 0-1.0
        """
        score = 0
        
        # Metric 1: Hard conflicts (binary, 100% weight)
        if self.metrics['hard_conflicts']['passed']:
            score += 100
        logger.debug(f"Hard conflicts contribution: {score}")
        
        # Metric 2: Gap minimization (continuous, 50% weight)
        gap_value = self.metrics['gap_minimization']['actual'] or 0
        score += gap_value * 50  # If score is 0.8, contributes 40 points
        logger.debug(f"Gap minimization contribution: {gap_value * 50}")
        
        # Metric 3: Distribution (binary, 30% weight)
        if self.metrics['distribution']['passed']:
            score += 30
        logger.debug(f"Distribution contribution: {score - (100 + gap_value * 50 + 0)}")
        
        # Metric 4: Execution time (binary, 20% weight)
        if self.metrics['execution_time']['passed']:
            score += 20
        logger.debug(f"Execution time contribution: {20 if self.metrics['execution_time']['passed'] else 0}")
        
        # Normalize to 0-1.0
        max_score = 200
        normalized_score = score / max_score
        
        return normalized_score
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive metrics report."""
        weighted_score = self.calculate_weighted_score()
        
        # Determine pass/fail status
        all_critical_passed = self.metrics['hard_conflicts']['passed']
        high_priority_passed = self.metrics['gap_minimization']['passed']
        
        overall_status = "PASS" if (all_critical_passed and high_priority_passed) else "FAIL"
        
        report = {
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'overall_status': overall_status,
            'weighted_score': weighted_score,
            'metrics': {}
        }
        
        # Detail each metric
        for metric_name, metric_data in self.metrics.items():
            report['metrics'][metric_name] = {
                'target': metric_data['target'],
                'actual': metric_data['actual'],
                'weight': metric_data['weight'],
                'passed': metric_data['passed'],
                'status': 'PASS' if metric_data['passed'] else 'FAIL'
            }
        
        return report
    
    def print_report(self, report: Dict = None):
        """Print human-readable metrics report."""
        if report is None:
            report = self.generate_report()
        
        print("\n" + "="*80)
        print("TIMETABLE METRICS VALIDATION REPORT")
        print("="*80)
        print(f"Timestamp: {report.get('timestamp', 'N/A')}")
        print(f"Overall Status: {report.get('overall_status', 'UNKNOWN')}")
        print(f"Weighted Score: {report.get('weighted_score', 0):.1%}")
        
        print("\n" + "METRIC DETAILS" + "-"*75)
        
       metrics = report.get('metrics', {})
        
        # Metric 1: Hard Conflicts
        m1 = metrics.get('hard_conflicts', {})
        status = "✓ PASS" if m1.get('passed') else "✗ FAIL"
        print(f"\n1. Hard Constraints (Critical, 100% weight): {status}")
        print(f"   Target: {m1.get('target', 'N/A')} conflicts")
        print(f"   Actual: {m1.get('actual', 'N/A')} conflicts")
        
        # Metric 2: Gap Minimization
        m2 = metrics.get('gap_minimization', {})
        status = "✓ PASS" if m2.get('passed') else "✗ FAIL"
        print(f"\n2. Gap Minimization (High Priority, 50% weight): {status}")
        print(f"   Target: > {m2.get('target', 'N/A'):.2f}")
        print(f"   Actual: {m2.get('actual', 'N/A'):.3f}")
        
        # Metric 3: Distribution
        m3 = metrics.get('distribution', {})
        status = "✓ PASS" if m3.get('passed') else "✗ FAIL"
        print(f"\n3. Load Distribution (Medium Priority, 30% weight): {status}")
        print(f"   Target: < {m3.get('target', 'N/A'):.2f} variance")
        print(f"   Actual: {m3.get('actual', 'N/A'):.3f} variance")
        
        # Metric 4: Execution Time
        m4 = metrics.get('execution_time', {})
        status = "✓ PASS" if m4.get('passed') else "✗ FAIL"
        print(f"\n4. Execution Time (Low Priority, 20% weight): {status}")
        print(f"   Target: < {m4.get('target', 'N/A')} seconds")
        print(f"   Actual: {m4.get('actual', 'N/A'):.2f} seconds")
        
        print("\n" + "="*80)
        print(f"FINAL RESULT: {report.get('overall_status', 'UNKNOWN')}")
        print("="*80 + "\n")
    
    def save_report(self, output_file: str = "./backend/analysis/metrics_report.json") -> Path:
        """Save report to JSON file."""
        report = self.generate_report()
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Report saved to {output_path}")
        return output_path


def run_validation_example():
    """Run example validation (demo without real data)."""
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    validator = MetricsValidator()
    
    # Mock timetable entries for demo
    class MockCourse:
        def __init__(self, id, name, class_size=30):
            self.id = id
            self.name = name
            self.class_size = class_size
    
    class MockLecturer:
        def __init__(self, id, name):
            self.id = id
            self.name = name
    
    class MockRoom:
        def __init__(self, id, name, capacity=50):
            self.id = id
            self.name = name
            self.capacity = capacity
    
    class MockTimeSlot:
        def __init__(self, id, day=0):
            self.id = id
            self.day = day
    
    class MockEntry:
        def __init__(self, course, lecturer, room, time_slot):
            self.course = course
            self.lecturer = lecturer
            self.room = room
            self.time_slot = time_slot
    
    # Create sample timetable
    entries = []
    for i in range(30):
        entry = MockEntry(
            course=MockCourse(i+1, f"Course{i+1}", 25 + (i % 20)),
            lecturer=MockLecturer((i % 10) + 1, f"Lecturer{(i % 10) + 1}"),
            room=MockRoom((i % 5) + 1, f"Room{(i % 5) + 1}", 50),
            time_slot=MockTimeSlot((i % 20) + 1, i % 5)
        )
        entries.append(entry)
    
    # Run validations
    start_time = time.time()
    
    validator.validate_hard_conflicts(entries)
    gap_score, _ = validator.validate_gap_minimization(entries)
    variance, _ = validator.validate_distribution(entries)
    
    end_time = time.time()
    
    validator.validate_execution_time(end_time, start_time)
    
    # Print report
    validator.print_report()
    validator.save_report()
    
    logger.info("Validation example complete!")


if __name__ == '__main__':
    run_validation_example()
