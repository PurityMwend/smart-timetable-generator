"""
Unified Data Pipeline for ML Training
Orchestrates: ITC XML → JSON, Synthetic generation, validation, standardization
"""

import sys
import logging
from pathlib import Path
from typing import List, Dict, Any
import json

# Add services to path
sys.path.insert(0, str(Path(__file__).parent))

from itc_xml_converter import convert_itc_xml_batch
from synthetic_data_generator import generate_synthetic_batch

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataPipeline:
    """Orchestrate complete data pipeline."""
    
    def __init__(self, base_dir: str = None):
        """Initialize pipeline with base directory."""
        if base_dir is None:
            # Find project root
            current = Path(__file__).parent
            while current != current.parent:
                if (current / ".git").exists():
                    base_dir = current
                    break
                current = current.parent
        
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent
        self.data_dir = self.base_dir / "backend" / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.itc_source = self.base_dir / "Data" / "ITC-data" / "20014070"
        self.itc_output = self.data_dir / "itc_json"
        self.synthetic_output = self.data_dir / "synthetic"
        self.combined_output = self.data_dir / "combined"
        
        logger.info(f"Pipeline initialized")
        logger.info(f"  Base dir: {self.base_dir}")
        logger.info(f"  Data dir: {self.data_dir}")
    
    def step1_convert_itc_xml(self) -> List[str]:
        """Step 1: Convert ITC XML files to JSON."""
        logger.info("\n" + "="*70)
        logger.info("STEP 1: Convert ITC XML to JSON")
        logger.info("="*70)
        
        if not self.itc_source.exists():
            logger.error(f"ITC source not found: {self.itc_source}")
            return []
        
        logger.info(f"Converting ITC XMLs from: {self.itc_source}")
        converted = convert_itc_xml_batch(str(self.itc_source), str(self.itc_output))
        
        logger.info(f"\n✓ STEP 1 COMPLETE: Converted {len(converted)} ITC files")
        return converted
    
    def step2_generate_synthetic(self, num_instances: int = 15) -> List[str]:
        """Step 2: Generate synthetic timetable data."""
        logger.info("\n" + "="*70)
        logger.info("STEP 2: Generate Synthetic Data")
        logger.info("="*70)
        
        variations = [
            {"courses": 50, "lecturers": 15, "rooms": 10, "students": 200},
            {"courses": 100, "lecturers": 30, "rooms": 20, "students": 500},
            {"courses": 200, "lecturers": 50, "rooms": 30, "students": 1000},
        ]
        
        logger.info(f"Generating {num_instances} synthetic instances...")
        generated = generate_synthetic_batch(str(self.synthetic_output), 
                                             num_instances=num_instances,
                                             variations=variations)
        
        logger.info(f"\n✓ STEP 2 COMPLETE: Generated {len(generated)} synthetic files")
        return generated
    
    def step3_validate_json_schema(self, json_files: List[str]) -> Dict[str, Any]:
        """Step 3: Validate JSON schema consistency."""
        logger.info("\n" + "="*70)
        logger.info("STEP 3: Validate JSON Schema")
        logger.info("="*70)
        
        required_keys = {"metadata", "rooms", "timeslots", "courses", 
                        "students", "constraints", "statistics"}
        
        validation_results = {
            "total_files": len(json_files),
            "valid_files": 0,
            "invalid_files": 0,
            "issues": []
        }
        
        for json_file in json_files:
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                # Check required keys
                missing_keys = required_keys - set(data.keys())
                if missing_keys:
                    validation_results["issues"].append({
                        "file": Path(json_file).name,
                        "issue": f"Missing keys: {missing_keys}"
                    })
                    validation_results["invalid_files"] += 1
                else:
                    validation_results["valid_files"] += 1
                    logger.info(f"  ✓ {Path(json_file).name}")
            
            except json.JSONDecodeError as e:
                validation_results["issues"].append({
                    "file": Path(json_file).name,
                    "issue": f"JSON decode error: {e}"
                })
                validation_results["invalid_files"] += 1
            except Exception as e:
                validation_results["issues"].append({
                    "file": Path(json_file).name,
                    "issue": str(e)
                })
                validation_results["invalid_files"] += 1
        
        logger.info(f"\nValidation Summary:")
        logger.info(f"  Valid: {validation_results['valid_files']}")
        logger.info(f"  Invalid: {validation_results['invalid_files']}")
        
        if validation_results["issues"]:
            logger.warning(f"  Issues found:")
            for issue in validation_results["issues"][:5]:
                logger.warning(f"    - {issue['file']}: {issue['issue']}")
        
        logger.info(f"\n✓ STEP 3 COMPLETE: Validation done")
        return validation_results
    
    def step4_generate_training_metadata(self, 
                                        itc_files: List[str],
                                        synthetic_files: List[str]) -> Dict[str, Any]:
        """Step 4: Generate metadata for ML training dataset."""
        logger.info("\n" + "="*70)
        logger.info("STEP 4: Generate Training Metadata")
        logger.info("="*70)
        
        # Collect statistics from all files
        all_files = itc_files + synthetic_files
        dataset_stats = {
            "total_instances": len(all_files),
            "itc_instances": len(itc_files),
            "synthetic_instances": len(synthetic_files),
            "instances": []
        }
        
        for json_file in all_files:
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                instance_info = {
                    "file": Path(json_file).name,
                    "source": data['metadata'].get('source', 'unknown'),
                    "problem_name": data['metadata']['problem'].get('problem_name', ''),
                    "statistics": data.get('statistics', {})
                }
                dataset_stats["instances"].append(instance_info)
            except Exception as e:
                logger.warning(f"Could not read {json_file}: {e}")
        
        # Aggregate statistics
        if dataset_stats["instances"]:
            avg_courses = sum(i['statistics'].get('total_courses', 0) 
                             for i in dataset_stats["instances"]) / len(dataset_stats["instances"])
            avg_students = sum(i['statistics'].get('total_students', 0) 
                              for i in dataset_stats["instances"]) / len(dataset_stats["instances"])
            
            dataset_stats["aggregate_stats"] = {
                "avg_courses_per_instance": round(avg_courses, 1),
                "avg_students_per_instance": round(avg_students, 1),
                "total_aggregate_courses": sum(i['statistics'].get('total_courses', 0) 
                                              for i in dataset_stats["instances"]),
                "total_aggregate_students": sum(i['statistics'].get('total_students', 0) 
                                               for i in dataset_stats["instances"])
            }
        
        logger.info(f"Dataset Summary:")
        logger.info(f"  Total instances: {dataset_stats['total_instances']}")
        logger.info(f"  ITC instances: {dataset_stats['itc_instances']}")
        logger.info(f"  Synthetic instances: {dataset_stats['synthetic_instances']}")
        if "aggregate_stats" in dataset_stats:
            stats = dataset_stats["aggregate_stats"]
            logger.info(f"  Avg courses/instance: {stats['avg_courses_per_instance']}")
            logger.info(f"  Avg students/instance: {stats['avg_students_per_instance']}")
        
        logger.info(f"\n✓ STEP 4 COMPLETE: Metadata generated")
        return dataset_stats
    
    def step5_create_dataset_split(self, 
                                   itc_files: List[str],
                                   synthetic_files: List[str]) -> Dict[str, List[str]]:
        """Step 5: Create train/validation/test split."""
        logger.info("\n" + "="*70)
        logger.info("STEP 5: Create Dataset Split (70/15/15)")
        logger.info("="*70)
        
        import random
        random.seed(42)
        
        all_files = itc_files + synthetic_files
        random.shuffle(all_files)
        
        total = len(all_files)
        train_size = int(total * 0.7)
        val_size = int(total * 0.15)
        
        split = {
            "train": all_files[:train_size],
            "validation": all_files[train_size:train_size + val_size],
            "test": all_files[train_size + val_size:]
        }
        
        logger.info(f"Dataset split:")
        logger.info(f"  Train: {len(split['train'])} ({len(split['train'])/total*100:.1f}%)")
        logger.info(f"  Validation: {len(split['validation'])} ({len(split['validation'])/total*100:.1f}%)")
        logger.info(f"  Test: {len(split['test'])} ({len(split['test'])/total*100:.1f}%)")
        
        # Save split info
        split_file = self.data_dir / "dataset_split.json"
        with open(split_file, 'w') as f:
            json.dump(split, f, indent=2)
        logger.info(f"  Saved split to: {split_file}")
        
        logger.info(f"\n✓ STEP 5 COMPLETE: Dataset split created")
        return split
    
    def run_full_pipeline(self, num_synthetic: int = 15) -> Dict[str, Any]:
        """Run complete pipeline."""
        logger.info("\n" + "="*70)
        logger.info("SMART TIMETABLE GENERATOR - DATA PIPELINE")
        logger.info("="*70)
        
        pipeline_results = {
            "status": "started",
            "steps": {}
        }
        
        try:
            # Step 1
            itc_files = self.step1_convert_itc_xml()
            pipeline_results["steps"]["itc_conversion"] = {
                "status": "complete",
                "files_converted": len(itc_files)
            }
            
            # Step 2
            synthetic_files = self.step2_generate_synthetic(num_synthetic)
            pipeline_results["steps"]["synthetic_generation"] = {
                "status": "complete",
                "files_generated": len(synthetic_files)
            }
            
            # Step 3
            all_files = itc_files + synthetic_files
            validation = self.step3_validate_json_schema(all_files)
            pipeline_results["steps"]["validation"] = {
                "status": "complete",
                "valid_files": validation["valid_files"],
                "invalid_files": validation["invalid_files"]
            }
            
            # Step 4
            training_meta = self.step4_generate_training_metadata(itc_files, synthetic_files)
            pipeline_results["steps"]["training_metadata"] = {
                "status": "complete",
                "total_instances": training_meta["total_instances"]
            }
            
            # Step 5
            split = self.step5_create_dataset_split(itc_files, synthetic_files)
            pipeline_results["steps"]["dataset_split"] = {
                "status": "complete",
                "train_size": len(split["train"]),
                "val_size": len(split["validation"]),
                "test_size": len(split["test"])
            }
            
            pipeline_results["status"] = "complete"
        
        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            pipeline_results["status"] = "failed"
            pipeline_results["error"] = str(e)
        
        return pipeline_results


def main():
    """Main entry point."""
    pipeline = DataPipeline()
    results = pipeline.run_full_pipeline(num_synthetic=15)
    
    print("\n" + "="*70)
    print("PIPELINE RESULTS")
    print("="*70)
    print(json.dumps(results, indent=2))
    
    if results["status"] == "complete":
        print("\n✓ DATA PIPELINE SUCCESSFUL!")
        print(f"Total instances ready for ML training: {results['steps']['dataset_split']['train_size'] + results['steps']['dataset_split']['val_size']}")
        print(f"Data directory: {pipeline.data_dir}")
    else:
        print("\n✗ PIPELINE FAILED")
        if "error" in results:
            print(f"Error: {results['error']}")


if __name__ == "__main__":
    main()
