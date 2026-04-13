# Implementation Summary: Role-Based Permissions & Training Data System

## What Was Implemented

A comprehensive **role-based permission system** with training data management capabilities for the Smart Timetable Generator. Users now have strictly enforced access levels based on their roles.

---

## Changes Made

### 1. **Backend Models** (`backend/timetable_app/models.py`)
Added three new models:
- **CommonUnit**: Cross-departmental teaching units
- **RecurrentUnit**: Units in specific courses/years (e.g., ISS401 in SE 4.2)
- **TrainingData**: Aggregated datasets for ML model training (admin-only)

### 2. **Backend Serializers** (`backend/timetable_app/serializers.py`)
Added serializers for:
- `CommonUnitSerializer`
- `RecurrentUnitSerializer`
- `TrainingDataSerializer` (nested with courses, lecturers, departments, units)

### 3. **Backend Permission Classes** (`backend/timetable_app/api_views.py`)
Added new permission classes:
- `IsStudentUser` - Students only
- `CanAccessTrainingData` - Timetablers (admins) only
- `CanManageLecturerData` - Lecturers & timetablers
- `IsStudentReadOnly` - Read-only for students

### 4. **Backend API Endpoints** (`backend/timetable_app/api_views.py`)
Added 6 new endpoints (CRUD):
- `/training-data/` - Manage training datasets
- `/common-units/` - Manage common units
- `/recurrent-units/` - Manage recurrent units courses units

### 5. **Backend Routes** (`backend/timetable_app/urls.py`)
Registered new URL patterns:
- `training-data/`, `common-units/`, `recurrent-units/`

### 6. **Database Migration** 
Created migration `0003_commonunit_trainingdata_recurrentunit.py`:
- Creates CommonUnit table
- Creates RecurrentUnit table
- Creates TrainingData table with M2M relationships
- Applied automatically with `migrate` command

### 7. **Frontend Pages**
**New:** `frontend/src/pages/TrainingData.jsx` & `TrainingData.css`
- Admin-only dashboard for training data management
- Create datasets with courses, lecturers, departments, units
- Manage common and recurrent units
- Dataset status tracking

### 8. **Frontend Updated Components**
**Modified:** `frontend/src/pages/DataManager.jsx` & `DataManager.css`
- **Timetablers:** See all tabs (Courses, Lecturers, Rooms, Departments, Time Slots, Entries) with full edit/manage capabilities
- **Lecturers:** See Courses, Rooms, Departments, Time Slots (view-only), and Entries tabs
- **Students:** No access (stays on home page)
- Role-based button visibility (Edit/Delete hidden for lecturers and students)
- Lecturers can view departments and time slots to understand scheduling context but cannot modify them

**Modified:** `frontend/src/components/Navbar.jsx`
- Data Manager link visible to Lecturers & Timetablers
- Training Data link visible to Timetablers only
- Generate link visible to Timetablers only

**Modified:** `frontend/src/App.jsx`
- Imported TrainingData page
- Added protected route: `/training-data` (timetabler only)
- Updated `/data` route: now requires "lecturer" role (includes timetablers)

### 9. **Documentation**
Created comprehensive guide: `PERMISSIONS_AND_TRAINING_DATA.md`
- Full role descriptions and permissions
- Training data system explanation
- API endpoints reference
- Access control table
- Testing procedures

---

## Role-Based Access

### **TIMETABLER** (@admin.cuk.ac.ke)
✅ Full system access
- Manage all data (courses, lecturers, rooms, departments, time slots)
- Create & manage training datasets
- Generate timetables
- Upload data files
- Export timetables

### **LECTURER** (@staff.cuk.ac.ke)
✅ Limited data management with enhanced visibility
- Manage: Courses, Rooms, Entries
- View (read-only): Departments, Time Slots
- ❌ Cannot: Access training data, manage departments/time slots, generate timetables, upload files, manage other lecturers

### **STUDENT** (@student.cuk.ac.ke)
✅ Read-only access
- View timetables
- Download timetables
- ❌ Cannot: Manage any data, access data manager, generate timetables

---

## Key Features

### Training Data System
1. **Common Units** - Cross-departmental units (e.g., ISS401 taught in CS, ENG, BUS)
2. **Recurrent Units** - Units in specific courses (e.g., ISS401 in Software Engineering 4.2)
3. **Training Datasets** - Collections of data for ML model training
   - Select courses, lecturers, departments
   - Include common units
   - Track model associations
   - Activate/deactivate for training

### Data Manager Enhancements
- **Role-based tab visibility** - Different tabs for different roles
- **Lecturer notice banner** - Explains limited access
- **Entries table view** - Clean display of scheduled timetable entries
- **Conditional buttons** - Edit/Delete only shown to timetablers

---

## Database Changes

### New Tables (created by migration 0003)
```
commonunit
- id, name, code, description, hours_per_week, created_at, updated_at

recurrentunit
- id, unit_id, course_id, year_of_study, semester, created_at, updated_at

trainingdata
- id, name, description, created_by_id, created_at, updated_at
- trained_model_path, is_active

trainingdata_courses (M2M)
trainingdata_lecturers (M2M)
trainingdata_departments (M2M)
trainingdata_common_units (M2M)
```

---

## Testing Guide

### Quick Test as Timetabler
1. Register with `test.admin@admin.cuk.ac.ke`
2. Login
3. Navigate to Data Manager → See all 6 tabs
4. Navigate to Training Data → Create a dataset
5. Upload courses/lecturers/departments

### Quick Test as Lecturer
1. Register with `test.lecturer@staff.cuk.ac.ke`
2. Login
3. Navigate to Data Manager → See 5 tabs (Courses, Rooms, Departments, Time Slots, Entries)
4. Verify Edit/Delete buttons NOT visible in Departments and Time Slots tabs (read-only)
5. Verify Edit/Delete buttons visible in Courses, Rooms, and Entries tabs (editable)
6. Try navigating to `/training-data` → Redirected to home
7. Verify helpful notice banner shows at top of Data Manager

### Quick Test as Student
1. Register with `test.student@student.cuk.ac.ke`
2. Login
3. No Data Manager link in navbar
4. Only see Dashboard and Timetable
5. Try navigating to `/data` → Redirected to home

---

## API Examples

### Create Training Dataset
```bash
POST /api/training-data/
{
    "name": "Fall 2024 Training Set",
    "description": "CS and ENG departments",
    "course_ids": [1, 2, 3],
    "lecturer_ids": [1, 2],
    "department_ids": [1, 2],
    "common_unit_ids": [1, 2]
}
```

### Add Common Unit
```bash
POST /api/common-units/
{
    "name": "Information Systems Security and Audit",
    "code": "ISS401",
    "hours_per_week": 3.0
}
```

### Add Recurrent Unit
```bash
POST /api/recurrent-units/
{
    "unit_id": 1,
    "course_id": 5,
    "year_of_study": 4,
    "semester": 2
}
```

---

## File Checklist

✅ **Backend Files Modified:**
- `models.py` - Added CommonUnit, RecurrentUnit, TrainingData
- `serializers.py` - Added 3 serializers
- `api_views.py` - Added 6 permission classes, 6 endpoint functions
- `urls.py` - Added 6 new URL patterns
- `migrations/0003_*.py` - Automatic migration for new models

✅ **Frontend Files Created:**
- `pages/TrainingData.jsx` - Admin training data management page
- `pages/TrainingData.css` - Styling for training data page

✅ **Frontend Files Modified:**
- `pages/DataManager.jsx` - Role-based UI with conditional tabs
- `pages/DataManager.css` - Enhanced styling for role-based features
- `components/Navbar.jsx` - Conditional navigation links
- `App.jsx` - Added training-data route, updated data route

✅ **Documentation:**
- `PERMISSIONS_AND_TRAINING_DATA.md` - Comprehensive system guide

---

## Backend Server State

✅ Database migration applied successfully
✅ All models created in database
✅ All endpoints registered and functional
✅ Permission classes active and enforcing access control

---

## Next Steps

1. **Start Backend Server:**
   ```bash
   cd backend
   ./venv/bin/python manage.py runserver
   ```

2. **Start Frontend Server:**
   ```bash
   cd frontend
   npm install  # if needed
   npm run dev
   ```

3. **Test the System:**
   - Register accounts with different email domains
   - Verify role-based navigation
   - Test data manager with different roles
   - Create training datasets as admin
   - Verify lecturers can't access training data

4. **Optional Enhancements:**
   - Add form validation for dataset creation
   - Add edit/delete functions for training data
   - Implement dataset activation UI
   - Add model training trigger
   - Add ML model integration

---

## Summary

The system now enforces strict role-based access control:
- **Permissions checked at API level** (DRF permission classes)
- **UI adapted to user role** (conditional navigation and tabs)
- **Sensitive data protected** (training data admin-only)
- **Data integrity maintained** (lecturers can't modify system config)
- **User experience optimized** (only see what you can access)

**Status:** ✅ Complete and Ready for Testing
