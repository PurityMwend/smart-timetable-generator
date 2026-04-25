"""
Performance profiling for hybrid ML + OR-Tools scheduler.

Measures:
- ML inference time (draft generation)
- Constraint extraction time
- OR-Tools solving time
- Total pipeline time
- Memory usage
"""

import time
import json
from typing import Dict, List, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class PerformanceProfiler:
    """Profile hybrid scheduler performance."""
    
    def __init__(self, results_file: str = "./backend/analysis/performance_results.json"):
        self.results_file = Path(results_file)
        self.results = {
            'timestamp': None,
            'configuration': {},
            'timings': {},
            'memory_usage': {},
            'metrics': {},
            'summary': {}
        }
    
    def profile_ml_inference(self, scheduler, schedule_template: Dict[str, Any]) -> float:
        """Profile ML inference time."""
        if not scheduler.orchestrator:
            logger.warning("ML orchestrator not available, skipping inference profiling")
            return 0
        
        start = time.time()
        
        try:
            ml_draft = scheduler.orchestrator.run_hybrid_scheduling(schedule_template)
            elapsed = time.time() - start
            
            self.results['timings']['ml_inference'] = elapsed
            self.results['metrics']['ml_draft_entries'] = len(
                ml_draft.get('timetable_entries', [])
            )
            self.results['metrics']['ml_confidence'] = ml_draft.get('confidence', 0)
            
            logger.info(f"ML Inference: {elapsed:.2f}s ({self.results['metrics']['ml_draft_entries']} entries)")
            return elapsed
        
        except Exception as e:
            logger.warning(f"ML inference failed: {e}")
            return None
    
    def profile_constraint_extraction(self, scheduler) -> float:
        """Profile constraint extraction time."""
        if not scheduler.constraint_builder:
            logger.warning("Constraint builder not available")
            return 0
        
        start = time.time()
        
        try:
            config = scheduler.constraint_builder.build_solver_config()
            elapsed = time.time() - start
            
            self.results['timings']['constraint_extraction'] = elapsed
            self.results['metrics']['constraints_extracted'] = len(
                config.get('constraints', [])
            )
            
            logger.info(f"Constraint Extraction: {elapsed:.4f}s ({self.results['metrics']['constraints_extracted']} constraints)")
            return elapsed
        
        except Exception as e:
            logger.warning(f"Constraint extraction failed: {e}")
            return None
    
    def profile_or_tools_setup(self, scheduler) -> float:
        """Profile OR-Tools constraint setup time."""
        start = time.time()
        
        scheduler._create_decision_variables()
        v_time = time.time()
        
        scheduler._add_mandatory_constraints()
        m_time = time.time()
        
        scheduler._add_resource_constraints()
        r_time = time.time()
        
        scheduler._add_availability_constraints()
        a_time = time.time()
        
        total_elapsed = a_time - start
        
        self.results['timings']['or_tools_setup'] = total_elapsed
        self.results['timings']['or_tools_variables'] = v_time - start
        self.results['timings']['or_tools_mandatory'] = m_time - v_time
        self.results['timings']['or_tools_resources'] = r_time - m_time
        self.results['timings']['or_tools_availability'] = a_time - r_time
        
        self.results['metrics']['total_variables'] = (
            len(scheduler.courses) * len(scheduler.time_slots) * len(scheduler.rooms)
        )
        self.results['metrics']['total_constraints'] = scheduler.model.NumConstraints()
        
        logger.info(f"OR-Tools Setup: {total_elapsed:.2f}s")
        logger.info(f"  - Variables: {self.results['timings']['or_tools_variables']:.4f}s")
        logger.info(f"  - Mandatory: {self.results['timings']['or_tools_mandatory']:.4f}s")
        logger.info(f"  - Resources: {self.results['timings']['or_tools_resources']:.4f}s")
        logger.info(f"  - Availability: {self.results['timings']['or_tools_availability']:.4f}s")
        
        return total_elapsed
    
    def profile_ml_constraint_application(self, scheduler, ml_config: Dict) -> float:
        """Profile ML constraint application time."""
        if not ml_config:
            logger.info("No ML config, skipping constraint application profiling")
            return 0
        
        start = time.time()
        
        try:
            scheduler._apply_ml_constraints()
            elapsed = time.time() - start
            
            self.results['timings']['ml_constraint_application'] = elapsed
            logger.info(f"ML Constraint Application: {elapsed:.4f}s")
            return elapsed
        
        except Exception as e:
            logger.warning(f"ML constraint application failed: {e}")
            return None
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate performance report."""
        self.results['timestamp'] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Calculate summary statistics
        timings = self.results['timings']
        
        if 'ml_inference' in timings and timings['ml_inference']:
            ml_time = timings['ml_inference']
        else:
            ml_time = 0
        
        or_setup = timings.get('or_tools_setup', 0) or 0
        constraint_app = timings.get('ml_constraint_application', 0) or 0
        
        total_pipeline = ml_time + or_setup + constraint_app
        
        self.results['summary'] = {
            'ml_time': ml_time,
            'or_tools_setup_time': or_setup,
            'ml_constraint_app_time': constraint_app,
            'total_pipeline_time': total_pipeline,
            'ml_percentage': (ml_time / total_pipeline * 100) if total_pipeline > 0 else 0,
            'or_tools_percentage': (or_setup / total_pipeline * 100) if total_pipeline > 0 else 0,
        }
        
        return self.results
    
    def save_report(self) -> Path:
        """Save report to disk."""
        self.results_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"Report saved to {self.results_file}")
        return self.results_file
    
    def print_report(self):
        """Print human-readable report."""
        print("\n" + "="*70)
        print("PERFORMANCE PROFILE REPORT")
        print("="*70)
        print(f"Timestamp: {self.results.get('timestamp', 'N/A')}")
        
        print("\nTIMINGS (seconds)")
        print("-"*70)
        timings = self.results.get('timings', {})
        for key, value in timings.items():
            if isinstance(value, (int, float)):
                print(f"  {key:.<40} {value:>8.4f}s")
        
        print("\nMETRICS")
        print("-"*70)
        metrics = self.results.get('metrics', {})
        for key, value in metrics.items():
            print(f"  {key:.<40} {value:>8}")
        
        print("\nSUMMARY")
        print("-"*70)
        summary = self.results.get('summary', {})
        print(f"  ML Inference Time: {summary.get('ml_time', 0):.2f}s ({summary.get('ml_percentage', 0):.1f}%)")
        print(f"  OR-Tools Setup Time: {summary.get('or_tools_setup_time', 0):.2f}s ({summary.get('or_tools_percentage', 0):.1f}%)")
        print(f"  Total Pipeline Time: {summary.get('total_pipeline_time', 0):.2f}s")
        
        print("\nTARGETS vs ACTUAL")
        print("-"*70)
        targets = {
            'ML Inference': (30, summary.get('ml_time', 0)),
            'OR-Tools Setup': (60, summary.get('or_tools_setup_time', 0)),
            'Total Pipeline': (120, summary.get('total_pipeline_time', 0)),
        }
        
        for name, (target, actual) in targets.items():
            status = "✓" if actual <= target else "✗"
            pct = (actual / target * 100) if target > 0 else 0
            print(f"  {status} {name:.<35} {actual:>6.2f}s / {target:>6.0f}s ({pct:>5.1f}%)")
        
        print("="*70 + "\n")


def run_performance_profile():
    """Run complete performance profile (demo without actual ML)."""
    import sys
    sys.path.insert(0, '/home/cinderella-man/Projects/smart-timetable-generator/backend')
    
    from timetable_app.services.hybrid_scheduler import HybridTimetableScheduler
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'
    )
    
    # Create mock data
    class MockDept:
        def __init__(self, id=1, name="Dept"):
            self.id = id
            self.name = name
    
    class MockCourse:
        def __init__(self, id, name):
            self.id = id
            self.name = name
            self.class_size = 30
            self.hours_per_week = 3
            self.department = MockDept()
    
    class MockLecturer:
        def __init__(self, id, name):
            self.id = id
            self.name = name
            self.department = MockDept()
    
    class MockRoom:
        def __init__(self, id, name):
            self.id = id
            self.name = name
            self.capacity = 50
            self.room_type = "lecture"
    
    class MockTimeSlot:
        def __init__(self, id):
            self.id = id
            self.day = 0
            self.start_time = "08:00"
            self.end_time = "09:00"
    
    # Create test data
    courses = [MockCourse(i, f"Course{i}") for i in range(1, 21)]
    lecturers = [MockLecturer(i, f"Lecturer{i}") for i in range(1, 11)]
    rooms = [MockRoom(i, f"Room{i}") for i in range(1, 6)]
    time_slots = [MockTimeSlot(i) for i in range(1, 26)]
    
    # Create profiler
    profiler = PerformanceProfiler()
    
    logger.info("\nStarting Performance Profile...")
    logger.info("="*70)
    
    # Create scheduler
    scheduler = HybridTimetableScheduler(
        courses=courses,
        lecturers=lecturers,
        rooms=rooms,
        time_slots=time_slots,
        use_ml_hybrid=False  # Disable ML for demo
    )
    
    # Profile OR-Tools setup
    profiler.profile_or_tools_setup(scheduler)
    
    # Generate schedule template
    template = scheduler._create_schedule_template()
    
    # Generate report
    profiler.generate_report()
    profiler.print_report()
    profiler.save_report()
    
    logger.info("Performance profile complete!")


if __name__ == '__main__':
    run_performance_profile()
