"""
Aggregates all ITC + synthetic JSON files into all_training_data.json.
Also generates timetable_entries from course/timeslot data since
the ML models require them for feature extraction.
"""

import json
import random
from pathlib import Path

random.seed(42)

PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "backend" / "data"
OUTPUT_FILE = DATA_DIR / "all_training_data.json"

ITC_DIR = DATA_DIR / "itc_json"
SYNTHETIC_DIR = DATA_DIR / "synthetic"


def generate_entries(schedule: dict) -> list:
    """Generate timetable_entries from courses + rooms + timeslots."""
    courses = schedule.get('courses', [])
    rooms = schedule.get('rooms', [])
    timeslots = schedule.get('timeslots', [])

    if not courses or not rooms:
        return []

    # Build a pool of unique (day, start_time) slots from timeslots
    # Use only week 1 to avoid explosion
    slot_pool = []
    seen = set()
    for ts in timeslots:
        key = (ts.get('day_of_week', 0), ts.get('start_time', '08:00'))
        if key not in seen:
            seen.add(key)
            slot_pool.append(key)
    
    # Fallback if timeslots empty
    if not slot_pool:
        for day in range(5):
            for hour in range(8, 18):
                slot_pool.append((day, f"{hour:02d}:00"))

    entries = []
    for course in courses:
        # Pick a random slot and room
        day, start_time = random.choice(slot_pool)
        
        # Find a room with enough capacity
        class_size = course.get('class_size', 30)
        suitable = [r for r in rooms if r.get('capacity', 50) >= class_size]
        room = random.choice(suitable) if suitable else random.choice(rooms)

        # Parse end time
        try:
            h, m = map(int, start_time.split(':'))
            end_h = h + 1
            end_time = f"{end_h:02d}:{m:02d}"
        except:
            end_time = "09:00"

        entries.append({
            "course_id": course['id'],
            "room_id": room['id'],
            "day": day,
            "start_time": start_time,
            "end_time": end_time,
            "lecturer_id": course.get('lecturer_ids', [None])[0] if course.get('lecturer_ids') else None,
        })

    return entries


def load_and_prepare(filepath: Path) -> dict:
    """Load a JSON file and ensure it has timetable_entries."""
    with open(filepath) as f:
        data = json.load(f)

    if not data.get('timetable_entries'):
        data['timetable_entries'] = generate_entries(data)

    return data


def main():
    schedules = []
    errors = []

    sources = list(ITC_DIR.glob("*.json")) + list(SYNTHETIC_DIR.glob("*.json"))
    print(f"Found {len(sources)} source files")

    for filepath in sorted(sources):
        try:
            schedule = load_and_prepare(filepath)
            n_entries = len(schedule.get('timetable_entries', []))
            n_courses = len(schedule.get('courses', []))
            schedules.append(schedule)
            print(f"  ✓ {filepath.name}: {n_courses} courses, {n_entries} entries")
        except Exception as e:
            errors.append(filepath.name)
            print(f"  ✗ {filepath.name}: {e}")

    if errors:
        print(f"\nSkipped {len(errors)} files with errors: {errors}")

    output = {"schedules": schedules}
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output, f)

    size_mb = OUTPUT_FILE.stat().st_size / 1024 / 1024
    print(f"\n✓ Written {len(schedules)} schedules to {OUTPUT_FILE}")
    print(f"  File size: {size_mb:.1f} MB")


if __name__ == "__main__":
    main()
