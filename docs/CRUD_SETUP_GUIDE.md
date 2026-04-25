# Data Management CRUD Operations - Setup & Usage Guide

## Quick Start

### Prerequisites
- Backend running on `http://localhost:8000`
- Frontend running on `http://localhost:5174`
- Logged in as a **Timetabler** (admin user with @admin domain)

### Test Admin User
```
Email: admin@admin.ac.ke
Password: admin@admin.ac.ke (initial setup)
Role: Timetabler (Admin)
Access: Full CRUD on all entities
```

To set the password:
```bash
cd backend
python manage.py changepassword admin@admin.ac.ke
```

---

## What's New

The Data Manager now has **full CRUD functionality**:

✅ **CREATE** - Add new entities (Courses, Lecturers, Rooms, Departments, Time Slots, Entries)
✅ **READ** - View all entities in the database
✅ **UPDATE** - Edit existing entities
✅ **DELETE** - Remove entities with confirmation

---

## Features Overview

### 1. **Modal-Based Forms**
- Clean, user-friendly modal dialogs for adding/editing
- Form validation with error messages
- Required fields clearly marked
- Non-destructive (cancel without saving)

### 2. **Responsive UI**
- Works on desktop, tablet, and mobile
- List views with clear formatting
- Action buttons clearly visible
- Delete confirmation dialogs

### 3. **Permission-Based Access Control**
- Timetablers: Full CRUD access to all entities
- Lecturers: Read-only access (view only)
- Students: No Data Manager access

### 4. **API Integration**
- RESTful endpoints for all operations
- Session-based authentication
- CSRF token protection
- Proper HTTP methods (GET, POST, PUT, DELETE)

---

## How to Test CRUD Operations

### Test Dataset Created
```
✅ Department: TEST (Test Department)
✅ Course: TEST101 (Test Course)
✅ Entries: Ready for scheduling
```

### Step-by-Step Testing

#### 1. **Test Adding a Course**
1. Log in as `admin@admin.ac.ke`
2. Go to **Data Manager** → **Courses** tab
3. Click **"+ Add Course"**
4. Fill in:
   - Code: `CS201`
   - Name: `Web Development`
   - Department: Select "Test Department"
   - Year: 2
   - Class Size: 40
5. Click **"Save"**
6. ✅ Course should appear in the list

#### 2. **Test Editing a Course**
1. Find the course you just created (CS201)
2. Click **"Edit"**
3. Change Class Size to `45`
4. Click **"Save"**
5. ✅ Course should update in the list

#### 3. **Test Deleting a Course**
1. Find the course
2. Click **"Delete"**
3. Confirm the deletion
4. ✅ Course should disappear from the list

#### 4. **Test Adding a Lecturer**
1. Go to **Lecturers** tab (admin only)
2. Click **"+ Add Lecturer"**
3. Fill in:
   - Name: `Dr. John Smith`
   - Employee ID: `EMP-2024001`
   - Email: `john.smith@university.ac.ke`
   - Department: Select "Test Department"
4. Click **"Save"**
5. ✅ Lecturer should appear

#### 5. **Test Adding a Room**
1. Go to **Rooms** tab
2. Click **"+ Add Room"**
3. Fill in:
   - Name: `LT-201`
   - Building: `Main Block`
   - Capacity: `60`
   - Room Type: `Lecture Hall`
4. Click **"Save"**
5. ✅ Room should appear

#### 6. **Test Adding a Time Slot**
1. Go to **Time Slots** tab
2. Click **"+ Add Time Slot"**
3. Fill in:
   - Day: `Monday`
   - Start Time: `09:00`
   - End Time: `10:00`
4. Click **"Save"**
5. ✅ Time Slot should appear

#### 7. **Test Adding a Timetable Entry**
1. Go to **Entries** tab
2. Click **"+ Add Entry"**
3. Fill in:
   - Course: `CS201 - Web Development`
   - Lecturer: `Dr. John Smith`
   - Room: `LT-201`
   - Time Slot: `Monday 09:00 - 10:00`
4. Click **"Save"**
5. ✅ Entry should appear in the table

#### 8. **Test Permission Denial**
1. Log out
2. Log in as a **Lecturer** (`lecturer@staff.ac.ke`)
3. Go to **Data Manager** → **Courses**
4. Try clicking **"+ Add Course"** (should not be visible)
5. ✅ Add button should not appear
6. ✅ Edit/Delete buttons should not appear

---

## API Endpoints Reference

### Course Management
```
GET    /api/courses/              - List all courses
POST   /api/courses/              - Create new course (Timetabler only)
PUT    /api/courses/{id}/         - Update course (Timetabler only)
DELETE /api/courses/{id}/         - Delete course (Timetabler only)
GET    /api/courses/{id}/         - Get course details
```

### Lecturer Management
```
GET    /api/lecturers/            - List all lecturers
POST   /api/lecturers/            - Create new lecturer (Timetabler only)
PUT    /api/lecturers/{id}/       - Update lecturer (Timetabler only)
DELETE /api/lecturers/{id}/       - Delete lecturer (Timetabler only)
GET    /api/lecturers/{id}/       - Get lecturer details
```

### Room Management
```
GET    /api/rooms/                - List all rooms
POST   /api/rooms/                - Create new room (Timetabler only)
PUT    /api/rooms/{id}/           - Update room (Timetabler only)
DELETE /api/rooms/{id}/           - Delete room (Timetabler only)
GET    /api/rooms/{id}/           - Get room details
```

### Department Management
```
GET    /api/departments/          - List all departments
POST   /api/departments/          - Create new department (Timetabler only)
PUT    /api/departments/{id}/     - Update department (Timetabler only)
DELETE /api/departments/{id}/     - Delete department (Timetabler only)
GET    /api/departments/{id}/     - Get department details
```

### Time Slot Management
```
GET    /api/timeslots/            - List all time slots
POST   /api/timeslots/            - Create new slot (Timetabler only)
PUT    /api/timeslots/{id}/       - Update slot (Timetabler only)
DELETE /api/timeslots/{id}/       - Delete slot (Timetabler only)
GET    /api/timeslots/{id}/       - Get slot details
```

### Timetable Entry Management
```
GET    /api/timetable-entries/    - List all entries
POST   /api/timetable-entries/    - Create new entry (Timetabler only)
PUT    /api/timetable-entries/{id}/ - Update entry (Timetabler only)
DELETE /api/timetable-entries/{id}/ - Delete entry (Timetabler only)
GET    /api/timetable-entries/{id}/ - Get entry details
```

---

## Response Examples

### Successful Creation (201 Created)
```json
{
  "id": 1,
  "code": "CS201",
  "name": "Web Development",
  "department": 3,
  "department_name": "Computer Science",
  "year_of_study": 2,
  "class_size": 40,
  "lecturers_count": 0
}
```

### Validation Error (400 Bad Request)
```json
{
  "code": ["course with this code already exists."],
  "name": ["This field may not be blank."]
}
```

### Permission Denied (403 Forbidden)
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### Not Found (404)
```json
{
  "detail": "Not found."
}
```

---

## Technical Architecture

### Frontend Components
```
/pages/DataManager.jsx
├── Main DataManager component
├── Modal form (EntityModal)
├── List components:
│   ├── CoursesList
│   ├── LecturersList
│   ├── RoomsList
│   ├── DepartmentsList
│   ├── TimeSlotsList
│   └── EntriesList
└── API calls via /services/api.js
```

### Backend Structure
```
/timetable_app/
├── models.py (Course, Lecturer, Room, etc)
├── serializers.py (ModelSerializers)
├── api_views.py (ViewSets with permissions)
├── urls.py (API routes)
└── permissions.py (IsTimetablerUser, IsTimetablerOrReadOnly)
```

### Permission Classes
```python
IsTimetablerUser
  - For sensitive operations (timetablers only)
  - Returns 403 if not timetabler

IsTimetablerOrReadOnly
  - For CRUD operations
  - GET: Authenticated users (any role)
  - POST/PUT/DELETE: Timetablers only
```

---

## Debugging & Troubleshooting

### Check Backend Logs
```bash
cd backend
tail -f path/to/django.log
```

### Test API Directly
```bash
# Get CSRF token
curl -c cookies.txt http://localhost:8000/api/auth/csrf-token/

# Login
curl -b cookies.txt -c cookies.txt \
  -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@admin.ac.ke","password":"password"}'

# Create course
curl -b cookies.txt \
  -X POST http://localhost:8000/api/courses/ \
  -H "Content-Type: application/json" \
  -d '{"code":"TEST","name":"Test","department":1,"year_of_study":1,"class_size":30}'
```

### Browser Console Debugging
1. Open Developer Tools (F12)
2. Go to **Network** tab
3. Watch API requests/responses
4. Check **Console** for JavaScript errors

### Common Issues

| Problem | Solution |
|---------|----------|
| 403 Forbidden | Verify you're logged in as timetabler |
| Modal not opening | Check browser console for JS errors |
| Changes not reflecting | Try refreshing the page or clearing cache |
| Field validation errors | Ensure all required fields are filled |
| 401 Unauthorized | Session expired, log in again |

---

## Performance Notes

### Optimization Done
- **N+1 Query Fix**: Using `select_related()` for foreign keys
- **Batch Operations**: Modal form reduces multiple HTTP roundtrips
- **Lazy Loading**: Data fetched on tab selection
- **Pagination Ready**: API supports pagination for large datasets

### For Production
- Add pagination (Django REST Framework provides this)
- Implement caching (Redis recommended)
- Add database indexes on frequently searched fields
- Monitor slow queries

---

## Next Steps After Setup

1. **Populate Test Data**
   - Add 5-10 departments
   - Add 20-30 courses
   - Add 10-15 lecturers
   - Add 15-20 rooms
   - Create standard time slots

2. **Schedule Classes**
   - Create timetable entries for all courses
   - Verify no conflicts exist
   - Export as PDF/Excel

3. **User Management**
   - Create user accounts for lecturers
   - Create student accounts
   - Verify permission restrictions work

4. **Testing**
   - Test all role-based access
   - Verify timetable generation
   - Check PDF/Excel exports

---

## Files Modified

### Frontend
- `/frontend/src/pages/DataManager.jsx` - Complete rewrite with CRUD
- `/frontend/src/pages/DataManager.css` - Enhanced styling for modals

### Documentation
- `/DATA_MANAGEMENT_GUIDE.md` - User guide
- This file - Technical setup guide

### No Backend Changes
Backend already had all necessary permissions and serializers configured!

---

## Support & Contact

For issues or questions:
1. Check the [DATA_MANAGEMENT_GUIDE.md](DATA_MANAGEMENT_GUIDE.md) for user help
2. Review browser console for errors
3. Check Django server logs
4. Review API endpoint responses

