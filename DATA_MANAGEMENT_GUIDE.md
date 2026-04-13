# Data Management Guide - CRUD Operations

## Overview
The Data Manager now provides full **Create, Read, Update, Delete (CRUD)** functionality for managing:
- Courses
- Lecturers (admin only)
- Rooms
- Departments
- Time Slots
- Timetable Entries

## Accessing the Data Manager
1. **Login** as a user with the `@admin` email domain (timetabler/admin role)
2. Navigate to the **"Data Manager"** page in the main menu
3. Select the entity you want to manage from the tabs

## Role-Based Permissions

### Timetabler (Admin) (@admin domain)
✅ **Full Access - Can:**
- View all entities
- Create new courses, lecturers, rooms, departments, time slots, entries
- Edit any entity
- Delete any entity

**Tabs Available:** Courses, Lecturers, Rooms, Departments, Time Slots, Entries

### Lecturer (@staff domain)
✅ **Read-Only Access - Can:**
- View courses, rooms, departments, time slots
- View timetable entries (read-only)

**Tabs Available:** Courses, Rooms, Departments, Time Slots, Entries

### Student (@student domain)
❌ **No Access** - Data Manager page not visible

---

## How to Use Each Entity

### 1. Adding a Course
1. Go to **Data Manager** → **Courses** tab
2. Click **"+ Add Course"** button
3. Fill in the form:
   - **Course Code** (e.g., "CS101") - Cannot be changed after creation
   - **Course Name** (e.g., "Intro to Programming")
   - **Department** - Select from dropdown
   - **Year of Study** (1-6) - Which year this course is for
   - **Class Size** - Expected number of students
4. Click **"Save"**

**Editing a Course:**
1. Click **"Edit"** on the course in the list
2. Modify any field except the Course Code
3. Click **"Save"**

**Deleting a Course:**
1. Click **"Delete"** on the course
2. Confirm the deletion in the popup

---

### 2. Adding a Lecturer
1. Go to **Data Manager** → **Lecturers** tab (admin only)
2. Click **"+ Add Lecturer"** button
3. Fill in the form:
   - **Name** (e.g., "Dr. Jane Smith")
   - **Employee ID** (e.g., "EMP-001") - Cannot be changed after creation
   - **Email** (optional) - e.g., "jane.smith@university.ac.ke"
   - **Department** - Select from dropdown
4. Click **"Save"**

**Editing a Lecturer:**
1. Click **"Edit"** on the lecturer
2. Modify name, email, or department
3. Click **"Save"**

**Deleting a Lecturer:**
1. Click **"Delete"** on the lecturer
2. Confirm the deletion

---

### 3. Adding a Room
1. Go to **Data Manager** → **Rooms** tab
2. Click **"+ Add Room"** button
3. Fill in the form:
   - **Room Name** (e.g., "LT-101", "Lab-A2")
   - **Building** (e.g., "Engineering Block")
   - **Capacity** - How many students can fit (default: 30)
   - **Room Type** - Select:
     - Lecture Hall
     - Lab
     - Seminar Room
     - Tutorial Room
4. Click **"Save"**

**Editing a Room:**
1. Click **"Edit"** on the room
2. Modify any field
3. Click **"Save"**

**Deleting a Room:**
1. Click **"Delete"** on the room
2. Confirm the deletion

---

### 4. Adding a Department
1. Go to **Data Manager** → **Departments** tab
2. Click **"+ Add Department"** button
3. Fill in the form:
   - **Department Code** (e.g., "CS", "ENG") - Cannot be changed after creation
   - **Department Name** (e.g., "Computer Science")
   - **School** - Select from dropdown (optional)
4. Click **"Save"**

**Editing a Department:**
1. Click **"Edit"** on the department
2. Modify name or school assignment
3. Click **"Save"**

**Deleting a Department:**
1. Click **"Delete"** on the department
2. Confirm the deletion

---

### 5. Adding a Time Slot
1. Go to **Data Manager** → **Time Slots** tab
2. Click **"+ Add Time Slot"** button
3. Fill in the form:
   - **Day** - Select from Monday to Saturday
   - **Start Time** - Click to set (e.g., 09:00)
   - **End Time** - Click to set (e.g., 10:00)
4. Click **"Save"**

**Example Time Slots:**
- Monday 09:00 - 10:00 (Morning Session)
- Monday 10:15 - 11:15 (Morning Session)
- Monday 14:00 - 15:00 (Afternoon Session)

**Editing a Time Slot:**
1. Click **"Edit"** on the time slot
2. Modify day or times
3. Click **"Save"**

**Deleting a Time Slot:**
1. Click **"Delete"** on the time slot
2. Confirm the deletion

---

### 6. Adding a Timetable Entry
1. Go to **Data Manager** → **Entries** tab
2. Click **"+ Add Entry"** button
3. Fill in the form:
   - **Course** - Select the course to schedule
   - **Lecturer** - Select the lecturer to assign
   - **Room** - Select the room where the class meets
   - **Time Slot** - Select when the class occurs
4. Click **"Save"**

**Example Entry:**
- Course: CS101 - Intro to Programming
- Lecturer: Dr. Jane Smith
- Room: LT-101
- Time Slot: Monday 09:00 - 10:00

**Editing an Entry:**
1. Click **"Edit"** on the entry
2. Modify any assignment
3. Click **"Save"**

**Deleting an Entry:**
1. Click **"Delete"** on the entry
2. Confirm the deletion

---

## Modal Form UI

### Features of the Add/Edit Modal:
- **Modal Overlay**: Darkened background prevents interaction with other elements
- **Close Button**: ✕ in top-right corner to cancel
- **Form Fields**: Organized input fields with proper labels
- **Validation**: Required fields are marked and validated
- **Error Messages**: Red error bar shows any submission errors
- **Action Buttons**:
  - **Save** - Submits the form
  - **Cancel** - Closes the modal without saving

### Form Field Types:
- **Text Input**: Course Name, Room Name, Lecturer Name, etc.
- **Number Input**: Year, Class Size, Capacity
- **Time Input**: Start time and End time for schedules
- **Dropdown/Select**: For relating entities (Department, School, etc.)

---

## API Endpoints Used

| Operation | HTTP Method | Endpoint | Permission |
|-----------|------------|----------|-----------|
| List Courses | GET | `/api/courses/` | Authenticated |
| Create Course | POST | `/api/courses/` | Timetabler |
| Update Course | PUT | `/api/courses/{id}/` | Timetabler |
| Delete Course | DELETE | `/api/courses/{id}/` | Timetabler |
| List Lecturers | GET | `/api/lecturers/` | Authenticated |
| Create Lecturer | POST | `/api/lecturers/` | Timetabler |
| Update Lecturer | PUT | `/api/lecturers/{id}/` | Timetabler |
| Delete Lecturer | DELETE | `/api/lecturers/{id}/` | Timetabler |
| List Rooms | GET | `/api/rooms/` | Authenticated |
| Create Room | POST | `/api/rooms/` | Timetabler |
| Update Room | PUT | `/api/rooms/{id}/` | Timetabler |
| Delete Room | DELETE | `/api/rooms/{id}/` | Timetabler |
| List Departments | GET | `/api/departments/` | Authenticated |
| Create Department | POST | `/api/departments/` | Timetabler |
| Update Department | PUT | `/api/departments/{id}/` | Timetabler |
| Delete Department | DELETE | `/api/departments/{id}/` | Timetabler |
| List Time Slots | GET | `/api/timeslots/` | Authenticated |
| Create Time Slot | POST | `/api/timeslots/` | Timetabler |
| Update Time Slot | PUT | `/api/timeslots/{id}/` | Timetabler |
| Delete Time Slot | DELETE | `/api/timeslots/{id}/` | Timetabler |
| List Entries | GET | `/api/timetable-entries/` | Authenticated |
| Create Entry | POST | `/api/timetable-entries/` | Timetabler |
| Update Entry | PUT | `/api/timetable-entries/{id}/` | Timetabler |
| Delete Entry | DELETE | `/api/timetable-entries/{id}/` | Timetabler |

---

## Common Issues & Troubleshooting

### Issue: "Access Denied (403)" when trying to add/edit/delete
**Solution:** You must be logged in as a timetabler (@admin email domain). Other roles can only view data.

### Issue: Getting "This field is required" error
**Solution:** Make sure all marked required fields are filled in:
- Course Code (courses)
- Course Name (courses)
- Employee ID (lecturers)
- Lecturer Name (lecturers)
- Room Name (rooms)
- Department Code (departments)
- Department Name (departments)
- Day (time slots)
- Start/End Time (time slots)

### Issue: Cannot edit Course Code or Employee ID
**Solution:** These fields are locked after creation for data integrity. They uniquely identify the entity and cannot be changed.

### Issue: Modal form appears empty after clicking Edit
**Solution:** 
1. This shouldn't happen - try refreshing the page
2. Check browser console for any JavaScript errors
3. Verify you have permission to edit that entity

### Issue: Deleted item still appears in list
**Solution:** The page may not have refreshed immediately. Try:
1. Closing and reopening the tab
2. Clicking another tab and coming back
3. Refreshing the page (F5)

---

## Best Practices

1. **Add Departments First** - Create all departments before adding courses and lecturers
2. **Add Rooms Before Scheduling** - Have rooms set up before creating timetable entries
3. **Create Time Slots Consistently** - Use the same time slots across days for predictability
4. **Assign Courses to Departments** - Always assign courses to the correct department
5. **Verify Timetable Conflicts** - Check that lecturers and rooms aren't double-booked
6. **Regular Backups** - Use the training data upload to backup your schedule data

---

## Testing Accounts

To test the CRUD functionality:

### Admin (Timetabler) Account:
- **Email:** `admin@admin.ac.ke`
- **Role:** Full CRUD access
- **Permissions:** Can manage all entities

### Lecturer Account:
- **Email:** `lecturer@staff.ac.ke`
- **Role:** Read-only access
- **Permissions:** Can view but not modify

### Student Account:
- **Email:** `student@student.ac.ke`
- **Role:** No Data Manager access
- **Permissions:** None

---

## Next Steps

After setting up your courses, lecturers, rooms, and time slots:

1. **Create Timetable Entries** - Assign courses to lecturers, rooms, and times
2. **Export Schedule** - Download PDFs or Excel files of the timetable
3. **View Student Timetable** - Students can see their schedule
4. **Upload Training Data** - Use the training data upload feature for bulk imports

---

## Technical Implementation

### Frontend Technologies:
- React 18 + Vite
- Axios for API calls
- Modal component for forms
- State management with hooks

### Backend Technologies:
- Django REST Framework
- ModelViewSet for CRUD operations
- Custom permission classes
- Session-based authentication

### Database:
- SQLite (development)
- PostgreSQL (production ready)
- Migrations for schema management
