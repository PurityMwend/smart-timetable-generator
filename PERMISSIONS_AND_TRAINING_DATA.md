# Role-Based Permissions & Training Data System

## Overview

This document describes the comprehensive role-based permission system implemented for the Smart Timetable Generator. The system enforces strict access controls across the application, ensuring students can only view timetables, lecturers can manage specific data, and timetablers (admins) have full control.

## User Roles & Permissions

### 1. **TIMETABLER (Admin/Superuser)**
**Email Domain:** `@admin.cuk.ac.ke`

**Access Permissions:**
- ✅ Full access to Data Manager (manage courses, lecturers, rooms, departments, time slots)
- ✅ Access to Training Data tab (manage ML training datasets)
- ✅ Generate timetables
- ✅ Upload data files
- ✅ Export timetables (PDF/Excel)
- ✅ View and manage all timetable entries
- ✅ Access to all system features

**Navigation:**
```
Dashboard → Data Manager → Training Data → Generate → Timetable
```

**Data Manager Tabs Available:** Courses, Lecturers, Rooms, Departments, Time Slots, Entries

---

### 2. **LECTURER**
**Email Domain:** `@staff.cuk.ac.ke`

**Access Permissions:**
- ✅ Limited Data Manager (Courses, Rooms, Departments, Time Slots, Entries - view only for departments/time slots)
- ❌ NO access to Training Data
- ❌ NO access to Lecturers (other lecturers management)
- ✅ Can view timetables
- ✅ Can download timetables
- ❌ Cannot generate timetables
- ❌ Cannot upload data files
- ❌ Cannot create or modify departments or time slots

**Navigation:**
```
Dashboard → Data Manager → Timetable
```

**Data Manager Tabs Available:** 
- Courses (view/manage)
- Rooms (view/manage)
- Departments (view only)
- Time Slots (view only)
- Entries (view/manage)

**Why Limited Access?**
- Lecturers should only manage data relevant to their teaching
- Departments and time slots are view-only (system-level - admin only)
- Training data is sensitive and admin-only
- Timetable generation requires system-level knowledge
- Lecturers need to see departments and time slots to understand scheduling context

---

### 3. **STUDENT**
**Email Domain:** `@student.cuk.ac.ke`

**Access Permissions:**
- ✅ View vital course information (courses, rooms, departments)
- ✅ View timetable/schedule
- ✅ Download timetables
- ❌ NO access to Data Manager
- ❌ NO access to Training Data
- ❌ Cannot modify any data
- ✅ Read-only access to timetable information only
- ❌ Cannot see sensitive/non-vital data (lecturer management, system config, etc.)

**Navigation:**
```
Dashboard → Course Info → Timetable
```

**Student Profile Features:**
- **Course Information Tab** - View available courses (code, name, year, class size)
- **Rooms Tab** - View class locations (room name, building, capacity, type)
- **Departments Tab** - View departments (code, name)
- **Timetable Tab** - View their assigned schedule (course, day/time, room location)

**What Students See:**
- Only vital, publicly accessible information
- No sensitive data (lecturer details, training data, system configuration)
- Read-only view - no edit or delete capabilities
- Personal timetable integrated with course information

**Why Limited to Vital Data Only?**
- Students need only to know their schedule and course locations
- Sensitive data like lecturer management is not student-facing
- Training data and system configuration are admin-only
- Data integrity and privacy protection
- Focused user experience with only relevant information

---
- Students need only to know their schedule
- Data modification should be restricted to faculty
- Training data is not relevant to students

---

## Training Data System

### Purpose
The Training Data system stores historical and meta-information to train ML models for intelligent timetable scheduling optimization.

### Components

#### **1. Common Units**
Cross-departmental teaching units that appear in multiple programs.

**Example:**
- Unit Code: `ISS401`
- Unit Name: `Information Systems Security and Audit`
- Hours/Week: 3.0
- Taught in: CS, ENG, BUS departments

**Access:** Admin only

#### **2. Recurrent Units**
Units that appear in specific courses and academic years.

**Example:**
- Unit: `ISS401` (Information Systems Security and Audit)
- Course: `Software Engineering (CS410)`
- Year.Semester: `4.2`
- Taught by: Multiple lecturers (e.g., 3) but assigned to one per session

**Significance:** Helps identify recurring patterns in curriculum design and lecturer load distribution.

**Access:** Admin only

#### **3. Training Datasets**
Aggregated collections of courses, lecturers, departments, and units for ML training.

**What can be included:**
- Courses with year levels and class sizes
- Lecturers with departments and expertise areas
- Departments and organizational structure
- Common and recurrent units
- Historical allocation patterns

**Use Cases:**
- Train scheduling algorithms on realistic data
- Identify optimal room-course-time allocations
- Learn lecturer availability patterns
- Predict course conflicts and overlaps

**Access:** Admin only

---

## Frontend Implementation

### Updated Pages

#### **1. Data Manager** (`/data`)
**Route Protection:** Lecturers & Timetablers only

**Adaptive UI:**
- **For Timetablers:** Shows all 6 tabs (Courses, Lecturers, Rooms, Departments, Time Slots, Entries) + File Upload button
- **For Lecturers:** Shows only 3 tabs (Courses, Rooms, Entries) + Helpful notice banner
- **For Students:** Access Denied (redirected to home)

**Key Features:**
- Role-specific tab visibility
- Read-write access for timetablers
- Read-only context for lecturers (buttons hidden)
- Clean, organized data lists
- Entry management with table view

#### **2. Training Data Page** (`/training-data`)
**Route Protection:** Timetablers (admins) only

**Features:**
- Create and manage training datasets
- Select courses, lecturers, departments to include
- Manage common units (cross-departmental)
- View recurrent unit patterns
- Track model relationship to datasets
- Activate/deactivate datasets for training

**Tabs:**
1. **Training Datasets** - Create, view, and manage datasets
2. **Common Units** - Add and list cross-departmental units
3. **Recurrent Units** - View unit occurrences in courses

---

## Backend Implementation

### New Models

```python
# CommonUnit - Cross-departmental teaching units
class CommonUnit(models.Model):
    name: str (unique)
    code: str (unique)
    description: str (optional)
    hours_per_week: float
    created_at: datetime
    updated_at: datetime

# RecurrentUnit - Unit in specific course/year
class RecurrentUnit(models.Model):
    unit: ForeignKey(CommonUnit)
    course: ForeignKey(Course)
    year_of_study: int
    semester: int
    Unique: (unit, course, year_of_study, semester)

# TrainingData - Aggregated training dataset
class TrainingData(models.Model):
    name: str
    description: str
    courses: M2M(Course)
    lecturers: M2M(Lecturer)
    departments: M2M(Department)
    common_units: M2M(CommonUnit)
    created_by: ForeignKey(User)
    created_at: datetime
    updated_at: datetime
    trained_model_path: str (optional)
    is_active: bool
```

### New API Endpoints

#### Training Data CRUD
```
GET    /training-data/                      - List all datasets (admin only)
POST   /training-data/                      - Create new dataset (admin only)
GET    /training-data/<id>/                 - Get specific dataset (admin only)
PUT    /training-data/<id>/                 - Update dataset (admin only)
DELETE /training-data/<id>/                 - Delete dataset (admin only)
```

#### Common Units CRUD
```
GET    /common-units/                       - List all units (admin only)
POST   /common-units/                       - Create new unit (admin only)
GET    /common-units/<id>/                  - Get specific unit (admin only)
PUT    /common-units/<id>/                  - Update unit (admin only)
DELETE /common-units/<id>/                  - Delete unit (admin only)
```

#### Recurrent Units CRUD
```
GET    /recurrent-units/                    - List all recurrent units (admin only)
POST   /recurrent-units/                    - Create new recurrent unit (admin only)
GET    /recurrent-units/<id>/               - Get specific recurrent (admin only)
PUT    /recurrent-units/<id>/               - Update recurrent (admin only)
DELETE /recurrent-units/<id>/               - Delete recurrent (admin only)
```

### Permission Classes

New permission classes enforce access control:

```python
class CanAccessTrainingData(permissions.BasePermission):
    """Allow access to training data only to timetablers (admins)."""
    
class CanManageLecturerData(permissions.BasePermission):
    """Allow lecturers to manage only relevant data (courses, rooms, entries)."""
    
class IsStudentReadOnly(permissions.BasePermission):
    """Allow students read-only access to timetables."""
```

---

## Access Control Summary Table

| Feature | Timetabler | Lecturer | Student |
|---------|:----------:|:--------:|:-------:|
| Dashboard | ✅ | ✅ | ✅ |
| Data Manager | ✅ | ✅ (limited) | ❌ |
| Course Information | ✅ | ✅ | ✅ (vital only) |
| Training Data | ✅ | ❌ | ❌ |
| Generate Timetable | ✅ | ❌ | ❌ |
| View Timetable | ✅ | ✅ | ✅ |
| Download Timetable | ✅ | ✅ | ✅ |
| Manage Courses | ✅ | ✅ | ❌ |
| View Courses | ✅ | ✅ | ✅ (list only) |
| Manage Lecturers | ✅ | ❌ | ❌ |
| Manage Rooms | ✅ | ✅ | ❌ |
| View Rooms | ✅ | ✅ | ✅ (list only) |
| Manage Departments | ✅ | ❌ | ❌ |
| View Departments | ✅ | ✅ | ✅ (list only) |
| Manage Time Slots | ✅ | ❌ | ❌ |
| View Time Slots | ✅ | ✅ | ❌ |
| Manage Entries | ✅ | ✅ | ❌ |
| View Entries | ✅ | ✅ | ✅ (schedule only) |
| Upload Data | ✅ | ❌ | ❌ |

---

## Frontend Routes

### Protected Routes Configuration

```javascript
// Admin-only routes
/data          → PrivateRoute(requiredRole="timetabler")  → DataManager
/training-data → PrivateRoute(requiredRole="timetabler")  → TrainingData
/generate      → PrivateRoute(requiredRole="timetabler")  → TimetableGenerator

// Lecturer + Admin routes
/data          → PrivateRoute(requiredRole="lecturer")    → DataManager (limited)

// All authenticated users
/              → PrivateRoute()                           → Dashboard
/view          → PrivateRoute()                           → TimetableViewer
/student-info  → PrivateRoute()                           → StudentInformation

// Public routes
/login         → Login
/register      → Register
```

---

## Implementation Notes

### Frontend
1. **PrivateRoute Component** updated to support "lecturer" role requirement
2. **DataManager Component** adapted to show/hide tabs based on user role
3. **useAuth Hook** provides: `isTimetabler`, `isLecturer`, `isStudent`
4. **Navbar** dynamically shows navigation based on user role
5. **TrainingData Component** handles training dataset management UI

### Backend
1. **Permission Classes** checked at view level before execution
2. **Models** include proper relationships and constraints
3. **Serializers** handle nested data and role-specific fields
4. **Migrations** create required database tables (0003_*.py)
5. **API Views** return 403 Forbidden if user lacks permission

---

## Testing the System

### As Timetabler (Admin)
1. Register with email: `test@admin.cuk.ac.ke`
2. Login
3. Verify full navigation visible
4. Access all tabs in Data Manager
5. Access Training Data tab
6. Verify all endpoints return data

### As Lecturer
1. Register with email: `test@staff.cuk.ac.ke`
2. Login
3. Verify limited navigation (no Training Data, Generate)
4. Access Data Manager
5. Verify only Courses, Rooms, Entries visible
6. Verify Departments/Time Slots not accessible
7. Verify no upload button visible

### As Student
1. Register with email: `test@student.cuk.ac.ke`
2. Login
3. Verify limited navigation (only Dashboard, Timetable)
4. Verify Data Manager not accessible
5. Verify can view/download timetable
6. Verify read-only access

---

## Future Enhancements

1. **Lecturer-Specific Data:**
   - Show only courses they teach
   - Show only their availability
   - Limit entries to their assignments

2. **Student Enhancements:**
   - Filter timetable by their courses
   - Add to calendar feature
   - Send notifications

3. **Training Data:**
   - Auto-generate datasets from historical data
   - ML model integration for scheduling
   - Performance metrics dashboard

4. **Audit & Logging:**
   - Track who modifies what data
   - Export access logs
   - Admin dashboard for monitoring

---

## Database Schema Additions

Migration `0003_commonunit_trainingdata_recurrentunit.py` created:
- `timetable_app_commonunit` table
- `timetable_app_trainingdata` table
- `timetable_app_recurrentunit` table
- `timetable_app_trainingdata_courses` M2M table
- `timetable_app_trainingdata_lecturers` M2M table
- `timetable_app_trainingdata_departments` M2M table
- `timetable_app_trainingdata_common_units` M2M table

All tables automatically created with `python manage.py migrate`

---

## API Error Responses

### 403 Forbidden
```json
{
    "detail": "You do not have permission to perform this action."
}
```
**When:** User tries to access training-data without timetabler role

### 404 Not Found
```json
{
    "error": "Training dataset not found"
}
```
**When:** Resource doesn't exist or user lacks read permission

---

## Summary

The role-based system creates a secure, hierarchical access model:
- **Timetablers** manage all aspects and train ML models
- **Lecturers** contribute data relevant to their teaching
- **Students** consume generated schedules
- **Training Data** stays isolated to admin operations
- **Permissions** enforced at both API and UI levels

This ensures data integrity, security, and appropriate information disclosure.
