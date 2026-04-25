"""
Django management command for Phase 4: Complete End-to-End Pipeline Validation.

Usage:
    python manage.py run_phase4_validation --school-id=1
    python manage.py run_phase4_validation --school-id=1 --verbose
    python manage.py run_phase4_validation --generate-report
"""

import time
import json
from pathlib import Path
from typing import List, Dict, Any

from django.core.management.base import BaseCommand, CommandError
from django.db.models import QuerySet

from timetable_app.models import School, Course, Lecturer, Room, TimeSlot, TimetableEntry
from timetable_app.services.hybrid_scheduler import HybridTimetableScheduler
from timetable_app.analysis.metrics_validator import MetricsValidator
from timetable_app.analysis.performance_profile import PerformanceProfiler


class PhaseValidator:
    """Orchestrates Phase 4 validation."""
    
    def __init__(self, school_id: int, verbose: bool = False):
        self.school_id = school_id
        self.verbose = verbose
        self.school = None
        self.scheduler = None
        self.metrics_validator = None
        self.performance_profiler = None
        self.results = {
            'phase': 4,
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'school_id': school_id,
            'school_name': None,
            'pipeline_metrics': {},
            'success_metrics': {},
            'summary': {}
        }
    
    def log(self, message: str, level: str = "INFO"):
        """Log with optional verbosity control."""
        prefix = f"[{level}]" if self.verbose else ""
        print(f"{prefix} {message}")
    
    def validate_school_exists(self) -> bool:
        """Validate school exists."""
        self.log("Step 1: Validating school...")
        
        try:
            self.school = School.objects.get(id=self.school_id)
            self.results['school_name'] = self.school.name
            self.log(f"  ✓ School found: {self.school.name}")
            return True
        except School.DoesNotExist:
            raise CommandError(f"School with ID {self.school_id} not found")
    
    def load_school_data(self) -> bool:
        """Load all timetabling data for school."""
        self.log("Step 2: Loading school data...")
        
        courses = Course.objects.filter(department__school=self.school)
        lecturers = Lecturer.objects.filter(department__school=self.school)
        rooms = Room.objects.filter(school=self.school)
        time_slots = TimeSlot.objects.all()
        
        stats = {
            'courses': courses.count(),
            'lecturers': lecturers.count(),
            'rooms': rooms.count(),
            'time_slots': time_slots.count(),
        }
        
        self.log(f"  ✓ Loaded {stats['courses']} courses, {stats['lecturers']} lecturers, "
                f"{stats['rooms']} rooms, {stats['time_slots']} time slots")
        
        self.results['data_stats'] = stats
        
        return (courses, lecturers, rooms, time_slots)
    
    def initialize_scheduler(self, courses, lecturers, rooms, time_slots) -> bool:
        """Initialize hybrid scheduler."""
        self.log("Step 3: Initializing hybrid scheduler...")
        
        try:
            self.scheduler = HybridTimetableScheduler(
                courses=courses,
                lecturers=lecturers,
                rooms=rooms,
                time_slots=time_slots,
                use_ml_hybrid=True
            )
            
            stats = self.scheduler.get_statistics()
            self.log(f"  ✓ Scheduler initialized (ML enabled: {stats['ml_enabled']})")
            
            return True
        except Exception as e:
            raise CommandError(f"Failed to initialize scheduler: {str(e)}")
    
    def run_scheduling_pipeline(self) -> List:
        """Run main scheduling pipeline."""
        self.log("Step 4: Running scheduling pipeline...")
        
        # Record start time
        start_time = time.time()
        
        try:
            # Execute pipeline
            entries = self.scheduler.generate()
            
            # Record end time
            end_time = time.time()
            elapsed = end_time - start_time
            
            self.log(f"  ✓ Pipeline complete: {len(entries)} entries in {elapsed:.2f}s")
            
            # Store timing
            self.results['pipeline_metrics'] = {
                'entries_generated': len(entries),
                'execution_time': elapsed,
                'start_timestamp': time.time() - elapsed,
                'end_timestamp': time.time()
            }
            
            return entries, start_time, end_time
        
        except Exception as e:
            raise CommandError(f"Scheduling pipeline failed: {str(e)}")
    
    def validate_success_metrics(self, entries: List, start_time: float, end_time: float) -> bool:
        """Run all 4 success metrics validations."""
        self.log("Step 5: Validating success metrics...")
        
        self.metrics_validator = MetricsValidator()
        
        # Run all validations
        conflicts, m1_pass = self.metrics_validator.validate_hard_conflicts(entries)
        gap_score, m2_pass = self.metrics_validator.validate_gap_minimization(entries)
        variance, m3_pass = self.metrics_validator.validate_distribution(entries)
        exec_time, m4_pass = self.metrics_validator.validate_execution_time(end_time, start_time)
        
        # Store results
        metrics_report = self.metrics_validator.generate_report()
        self.results['success_metrics'] = metrics_report['metrics']
        
        # Summary
        all_passed = m1_pass and m2_pass and m3_pass and m4_pass
        critical_passed = m1_pass  # Hard conflicts are critical
        
        summary = {
            'overall_status': 'PASS' if all_passed else 'FAIL',
            'critical_passed': critical_passed,
            'all_metrics_passed': all_passed,
            'weighted_score': metrics_report['weighted_score'],
            'passing_metrics': sum([m1_pass, m2_pass, m3_pass, m4_pass]),
            'total_metrics': 4
        }
        
        self.results['summary'] = summary
        
        self.log(f"  Metrics: {summary['passing_metrics']}/{summary['total_metrics']} passed")
        self.log(f"  Critical passed (hard constraints): {critical_passed}")
        self.log(f"  Weighted score: {summary['weighted_score']:.1%}")
        
        return critical_passed
    
    def generate_final_report(self) -> Dict:
        """Generate comprehensive Phase 4 report."""
        report = self.results.copy()
        report['report_type'] = 'phase4_validation'
        report['completion_timestamp'] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        return report
    
    def save_results(self, output_dir: str = "./backend/analysis/phase4_results") -> Path:
        """Save Phase 4 results."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Main report
        report_file = output_dir / f"phase4_report_{time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.generate_final_report(), f, indent=2)
        
        self.log(f"  ✓ Report saved to {report_file}")
        
        return report_file
    
    def print_summary(self):
        """Print execution summary."""
        summary = self.results.get('summary', {})
        
        print("\n" + "="*80)
        print("PHASE 4 VALIDATION SUMMARY")
        print("="*80)
        print(f"School: {self.results.get('school_name', 'N/A')}")
        print(f"Timestamp: {self.results.get('timestamp', 'N/A')}")
        print(f"\nResult: {summary.get('overall_status', 'UNKNOWN')}")
        print(f"Weighted Score: {summary.get('weighted_score', 0):.1%}")
        print(f"Metrics Passed: {summary.get('passing_metrics', 0)}/{summary.get('total_metrics', 0)}")
        print("="*80 + "\n")
    
    def run(self) -> bool:
        """Execute complete Phase 4 validation."""
        try:
            # Step 1: Validate school
            self.validate_school_exists()
            
            # Step 2: Load data
            courses, lecturers, rooms, time_slots = self.load_school_data()
            
            # Step 3: Initialize scheduler
            self.initialize_scheduler(courses, lecturers, rooms, time_slots)
            
            # Step 4: Run pipeline
            entries, start_time, end_time = self.run_scheduling_pipeline()
            
            # Step 5: Validate metrics
            critical_passed = self.validate_success_metrics(entries, start_time, end_time)
            
            # Step 6: Save results
            self.save_results()
            
            # Print summary
            self.print_summary()
            
            return critical_passed
        
        except Exception as e:
            raise CommandError(f"Phase 4 validation failed: {str(e)}")


class Command(BaseCommand):
    """Django management command."""
    
    help = 'Run Phase 4: Complete end-to-end validation of hybrid scheduler'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--school-id',
            type=int,
            default=1,
            help='School ID to validate (default: 1)'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Verbose output'
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            default='./backend/analysis/phase4_results',
            help='Output directory for results'
        )
    
    def handle(self, *args, **options):
        school_id = options['school_id']
        verbose = options['verbose']
        
        try:
            # Create validator
            validator = PhaseValidator(school_id, verbose)
            
            # Run validation
            success = validator.run()
            
            # Return appropriate exit code
            if success:
                self.stdout.write(
                    self.style.SUCCESS(f'\n✓ Phase 4 validation completed successfully')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'\n⚠ Phase 4 validation completed with warnings')
                )
        
        except CommandError as e:
            self.stdout.write(self.style.ERROR(f'\n✗ Error: {str(e)}'))
            raise
