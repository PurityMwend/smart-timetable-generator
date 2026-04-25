# Training Data Upload Implementation

## Overview
The training data upload system is a complete backend pipeline for processing Excel/CSV files containing training data for the timetable scheduling system. This feature enables administrators (timetablers) to bulk-import courses, lecturers, departments, rooms, and other scheduling data.

## System Components

### 1. API Endpoints

#### POST `/api/upload/training-data/`
**Purpose:** Upload and process training datasets
**Authentication:** IsAuthenticated + IsTimetablerUser
**Request Body:**
```json
{
  "file": <binary file>,
  "file_type": "training_data",
  "description": "Optional description"
}
```
**Response (201):**
```json
{
  "message": "Training data imported successfully: X courses, Y lecturers, Z rooms",
  "data_summary": {
    "schools": [1, 2, 3],
    "departments": [5, 6, 7],
    "courses": [10, 11, 12],
    "lecturers": [20, 21, 22],
    "rooms": [30, 31]
  }
}
```
**Permissions:** Only timetablers can upload training data

#### POST `/api/upload/data/`
**Purpose:** General-purpose file upload for timetable data
**Authentication:** IsAuthenticated + IsTimetablerUser
**Request Body:** Same as above with `file_type: "timetable_data"`
**Response (201):** Returns parsed data summary

### 2. File Validation Layer (Serializers)

**FileUploadSerializer** validates incoming files:
- **Supported formats:** `.xlsx`, `.xls`, `.csv`, `.pdf` (extensions in extension validation list)
- **Maximum file size:** 50 MB
- **Validation rules:**
  - File field is required
  - File type must be either "training_data" or "timetable_data"
  - Description is optional
  - Extension validation against whitelist

### 3. File Parsing Service (FileParser)

#### Method: `parse_training_data_file(file)`
**Purpose:** Auto-detect file format and parse training data
**Returns:** `(success: bool, message: str, data_summary: dict)`

**Supported Formats:**
- **Excel (.xlsx, .xls):** Multi-sheet workbook with dedicated sheets for each entity:
  - `Schools` sheet: name, code, description
  - `Departments` sheet: name, code, school_code
  - `Courses` sheet: code, name, department_code, year, class_size
  - `Lecturers` sheet: name, employee_id, department_code, email
  - `Rooms` sheet: name, building, capacity, room_type

- **CSV (.csv):** Flat structure with headers:
  - Columns: course_code, course_name, year, class_size

**Data Processing:**
1. Auto-retrieves or creates entities in database
2. Returns IDs of created/retrieved objects in `data_summary`
3. Handles ForeignKey relationships (e.g., courses -> departments)
4. Supports department-to-school relationships

#### Method: `parse_timetable_data_file(file)`
**Purpose:** Parse Excel files for timetable scheduling
**Returns:** Same format as training data parser

**Excel Format:**
- `Timetable` sheet: course_code, lecturer_id, room_id, day
- Creates/updates TimetableEntry records
- Auto-creates TimeSlot if doesn't exist

### 4. Database Model Integration

**TrainingData Model** stores upload metadata:
```python
class TrainingData(models.Model):
    name = CharField()
    created_by = ForeignKey(User)
    is_active = BooleanField()
    courses = ManyToManyField(Course)
    lecturers = ManyToManyField(Lecturer)
    departments = ManyToManyField(Department)
```

## Workflow

### Upload Flow
```
1. Timetabler submits file via POST /api/upload/training-data/
2. FileUploadSerializer validates file:
   - Check extension
   - Check file size
   - Check file_type
3. upload_training_data() endpoint processes:
   - Calls FileParser.parse_training_data_file()
   - Gets back (success, message, data_summary)
   - If training_data type: Creates TrainingData record with M2M relationships
   - Returns 201 with data_summary
4. Frontend displays confirmation with import statistics
```

## Usage Examples

### Example Excel Structure (Training Data)
**Schools sheet:**
| name | code | description |
|------|------|-------------|
| School of Engineering | ENG | Engineering department |

**Departments sheet:**
| name | code | school_code |
|------|------|------------|
| Computer Science | CS | ENG |

**Courses sheet:**
| code | name | department_code | year | class_size |
|------|------|-----------------|------|-----------|
| CS101 | Intro to Programming | CS | 1 | 50 |

### Example CSV Structure (Training Data)
```csv
course_code,course_name,year,class_size
CS101,Intro to Programming,1,50
CS102,Data Structures,1,45
```

### Example Excel Structure (Timetable Data)
**Timetable sheet:**
| course_code | lecturer_id | room_id | day |
|-------------|------------|---------|-----|
| CS101 | 1 | 5 | Monday |
| CS102 | 2 | 6 | Tuesday |

## Error Handling

### Validation Errors (400)
- Invalid file extension
- File size exceeds 50 MB
- Unsupported file_type

### Processing Errors (500)
- Malformed Excel/CSV
- Missing required columns
- Database conflicts or integrity errors

Response format:
```json
{
  "error": "Error message describing what went wrong"
}
```

## Permissions

- **Required Role:** Timetabler (admin user)
- **Read-Only Access:** Lecturers and students cannot upload
- **Permission Class:** `IsTimetablerUser`

## Database Transactions

- File parsing is wrapped in transaction handling
- Each sheet is processed sequentially
- Failures are logged but don't roll back earlier sheets (consider this for future enhancement)

## Current Implementation Status

✅ **Completed:**
- URL routing for both endpoints
- FileUploadSerializer with validation
- API endpoint functions (upload_training_data, upload_data_file)
- FileParser.parse_training_data_file() method
- FileParser.parse_timetable_data_file() method
- Excel parsing for Schools, Departments, Courses, Lecturers, Rooms
- CSV parsing for basic course data
- Timetable data parsing and entry creation
- TrainingData record creation with M2M relationships
- Permission checks (IsAuthenticated + IsTimetablerUser)

⏳ **Pending:**
- Frontend TrainingDataUpload component with file drag-drop
- Sample training data Excel template
- Comprehensive error handling and logging
- Bulk import performance optimization for large files
- Transaction rollback on partial failures
- CSV parsing for full training data format

## Future Enhancements

1. **Template Generation:** Endpoint to download Excel template with correct structure
2. **Batch Processing:** Async task queue for processing large files
3. **Validation Report:** Detailed report of what was imported vs. what failed
4. **Update vs. Insert:** Smart handling of existing records (upsert logic)
5. **Sample Data:** Pre-built Excel files for testing
6. **UI Progress:** Real-time progress indicator for large uploads
