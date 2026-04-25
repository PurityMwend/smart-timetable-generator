"""
Django management command to train ML models.

Usage:
    python manage.py train_transformer_and_constraints
"""

from django.core.management.base import BaseCommand
from timetable_app.ml_models.training_pipeline import TrainingPipeline
from pathlib import Path
import os


class Command(BaseCommand):
    help = 'Train Transformer and constraint prediction models on JSON training data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--data-dir',
            type=str,
            default='./backend/data',
            help='Directory containing training JSON data (default: ./backend/data)'
        )
        parser.add_argument(
            '--models-dir',
            type=str,
            default='./backend/models',
            help='Directory to save trained models (default: ./backend/models)'
        )
        parser.add_argument(
            '--no-validate',
            action='store_true',
            help='Skip validation on test set'
        )

    def handle(self, *args, **options):
        data_dir = options['data_dir']
        models_dir = options['models_dir']

        self.stdout.write(self.style.SUCCESS("\n" + "="*70))
        self.stdout.write(self.style.SUCCESS("SMART TIMETABLE ML TRAINING"))
        self.stdout.write(self.style.SUCCESS("="*70))
        self.stdout.write(f"\nData directory: {data_dir}")
        self.stdout.write(f"Models directory: {models_dir}\n")

        # Run pipeline
        pipeline = TrainingPipeline(data_dir=data_dir, models_dir=models_dir)

        try:
            result = pipeline.run(verbose=True)

            if result['success']:
                self.stdout.write(self.style.SUCCESS("\n Training Complete!"))
                self.stdout.write(self.style.SUCCESS("\nModels saved:"))
                self.stdout.write(f"  • {Path(models_dir) / 'transformer_scheduler.pkl'}")
                self.stdout.write(f"  • {Path(models_dir) / 'conflict_predictor.pkl'}")
                self.stdout.write(f"  • {Path(models_dir) / 'gap_optimizer.pkl'}")
                self.stdout.write(f"  • {Path(models_dir) / 'load_balancer.pkl'}")
                self.stdout.write("\nNext steps:")
                self.stdout.write("  1. Review model performance in backend/analysis/model_validation.py")
                self.stdout.write("  2. Integrate models into scheduler in backend/timetable_app/services/scheduler.py")
            else:
                self.stdout.write(self.style.ERROR(f"\n Training failed: {result.get('error')}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n Error: {e}"))
            import traceback
            traceback.print_exc()
