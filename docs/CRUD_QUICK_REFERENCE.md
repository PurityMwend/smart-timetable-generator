# Quick Reference - CRUD Operations

## Getting Started

### Login
1. Navigate to http://localhost:5174
2. Enter credentials:
   - **Admin:** admin@admin.ac.ke / admin@admin.ac.ke
   - **Lecturer:** lecturer@staff.ac.ke / password
   - **Student:** student@student.ac.ke / password

### Access Data Manager
1. After login, click "Data Manager" in navigation menu
2. Select entity tab (Courses, Lecturers, Rooms, etc.)

---

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Close Modal | ESC |
| Submit Form | Ctrl+Enter |
| Refresh List | F5 |

---

## Entity Management Cheat Sheet

### 📚 Courses
- **Add:** Click "+ Add Course" → Fill form → Save
- **Edit:** Click "Edit" on course → Modify fields → Save
- **Delete:** Click "Delete" → Confirm
- **Required:** Code, Name, Department, Year, Class Size

### 👨‍🏫 Lecturers (Admin Only)
- **Add:** Click "+ Add Lecturer" → Fill form → Save
- **Edit:** Click "Edit" on lecturer → Change fields → Save
- **Delete:** Click "Delete" → Confirm
- **Required:** Name, Employee ID, Department

### 🏫 Rooms
- **Add:** Click "+ Add Room" → Fill form → Save
- **Edit:** Click "Edit" on room → Modify fields → Save
- **Delete:** Click "Delete" → Confirm
- **Required:** Name, Capacity, Room Type

### 🏢 Departments
- **Add:** Click "+ Add Department" → Fill form → Save
- **Edit:** Click "Edit" on dept → Change name/school → Save
- **Delete:** Click "Delete" → Confirm
- **Required:** Code, Name

### ⏰ Time Slots
- **Add:** Click "+ Add Time Slot" → Select day/time → Save
- **Edit:** Click "Edit" on slot → Change day/time → Save
- **Delete:** Click "Delete" → Confirm
- **Required:** Day, Start Time, End Time

### 📅 Timetable Entries
- **Add:** Click "+ Add Entry" → Select course/lecturer/room/time → Save
- **Edit:** Click "Edit" on entry → Change assignments → Save
- **Delete:** Click "Delete" → Confirm
- **Required:** Course, Lecturer, Room, Time Slot

---

## Form Field Types

### Text Input
- Course Code, Course Name, Lecturer Name, Room Name, etc.
- Type freely, no length limit
- Cannot contain special characters (validated)

### Number Input
- Year of Study, Class Size, Capacity
- Use up/down arrows or type directly
- Minimum 0, maximum varies by field

### Time Input
- Start Time, End Time
- Click to open time picker
- Format: HH:MM (24-hour)

### Dropdown Select
- Department, School, Room Type, etc.
- Click to open options
- Search by typing (some fields)

---

## Error Messages

| Error | Solution |
|-------|----------|
| "This field is required" | Fill in all required fields (marked with *) |
| "course with this code already exists" | Use a unique course code |
| "Invalid time" | Ensure start time < end time |
| "403 Forbidden" | Login as admin/timetabler (@admin domain) |
| "401 Unauthorized" | Session expired, login again |
| "Server Error (500)" | Check backend logs, try again |

---

## Common Tasks

### Add a Complete Course Schedule
```
1. Go to Departments tab → Create required departments
2. Go to Courses tab → Add all courses and assign to departments
3. Go to Lecturers tab → Add all lecturers
4. Go to Rooms tab → Create all classroom venues
5. Go to Time Slots tab → Create standard time slots
6. Go to Entries tab → Schedule each course
```

### Duplicate a Course
```
1. Note all fields of existing course
2. Click "Edit" to view details
3. Click "Cancel" to close without saving
4. Click "+ Add Course"
5. Re-enter same info but with new Course Code
6. Save as new course
```

### Delete All Test Data
```
1. Go to Entries tab → Delete all entries
2. Go to Courses tab → Delete all courses
3. Go to Time Slots tab → Delete all time slots
4. Go to Rooms tab → Delete all rooms
5. Go to Lecturers tab → Delete all lecturers
6. Go to Departments tab → Delete all departments (last)
```

---

## Data Validation Rules

| Field | Validation |
|-------|-----------|
| Course Code | Must be unique, 2-10 chars |
| Employee ID | Must be unique, 2-20 chars |
| Room Name | 1-100 characters |
| Capacity | Must be > 0 |
| Start Time | Must be < End Time |
| Email | Valid email format (optional) |

---

## Permission Levels

```
TIMETABLER (Admin - @admin domain)
├── ✅ View all data
├── ✅ Add courses, lecturers, rooms, etc.
├── ✅ Edit any entity
└── ✅ Delete any entity

LECTURER (@staff domain)
├── ✅ View courses, rooms, time slots
├── ✅ View own timetable entries
├── ❌ Cannot add/edit/delete
└── ❌ Cannot manage users

STUDENT (@student domain)
├── ✅ View personal timetable
├── ❌ Cannot access Data Manager
├── ❌ Cannot add/edit/delete
└── ❌ Cannot view other data
```

---

## Helpful Tips

✅ **Always create departments first** - Other entities depend on them
✅ **Use consistent naming** - Makes schedules easier to read
✅ **Create standard time slots** - Use same times across all days
✅ **Verify no conflicts** - Check lecturer/room aren't double-booked
✅ **Export regularly** - Download PDF/Excel for backup
✅ **Test with small dataset first** - Before adding full course list

---

## Troubleshooting

### Modal won't open?
- Check browser console (F12)
- Verify you have permission (timetabler only)
- Try refreshing the page

### Changes not saved?
- Check for error messages in modal
- Verify all required fields filled
- Look for red error bar at top of modal

### Button not working?
- Try clicking again (may be processing)
- Check internet connection
- Verify backend is running

### Need to undo deletion?
- Use database backup
- Or manually re-create the entity
- Or export previous training data

---

## Support

**Can't remember the password?**
Run: `python manage.py changepassword admin@admin.ac.ke`

**Need to create new admin?**
Run: `python manage.py createsuperuser`

**Database corrupted?**
Run: 
```bash
python manage.py migrate zero timetable_app
python manage.py migrate
```

---

## API Reference (For Developers)

```bash
# Get CSRF token
curl -X GET http://localhost:8000/api/auth/csrf-token/

# List courses
curl -X GET http://localhost:8000/api/courses/

# Create course (POST)
curl -X POST http://localhost:8000/api/courses/ \
  -d '{"code":"CS101","name":"Intro","department":1,...}'

# Update course (PUT)
curl -X PUT http://localhost:8000/api/courses/1/ \
  -d '{"code":"CS101","name":"Programming I",...}'

# Delete course (DELETE)
curl -X DELETE http://localhost:8000/api/courses/1/
```

---

## More Information

- **Full User Guide:** [DATA_MANAGEMENT_GUIDE.md](DATA_MANAGEMENT_GUIDE.md)
- **Technical Setup:** [CRUD_SETUP_GUIDE.md](CRUD_SETUP_GUIDE.md)
- **Complete Summary:** [CRUD_OPERATIONS_SUMMARY.md](CRUD_OPERATIONS_SUMMARY.md)
- **Training Data Upload:** [TRAINING_DATA_UPLOAD.md](TRAINING_DATA_UPLOAD.md)

