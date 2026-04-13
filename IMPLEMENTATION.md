# Smart Timetable Generator - Complete System Architecture

## Overview

A modern, enterprise-grade timetable generation system built with Django REST Framework and React, featuring intelligent constraint-based scheduling, role-based access control, and a beautiful school-themed interface.

**Color Scheme:** Academic Blue (#1f4788), Warm Orange (#FF9500), Fresh Green (#2ECC71)

---

## Backend Architecture

### Organized Module Structure

```
timetable_app/
├── models.py              # Core domain models (User, Course, Lecturer, Room, etc.)
├── serializers.py         # DRF serializers with built-in validation
├── api_views.py          # Clean, organized API endpoints (replaced monolithic views.py)
├── validators.py         # Business logic constraints and validations
├── admin.py              # Django admin interface
├── urls.py               # URL routing
├── services/             # NEW: Service layer for business logic
│   ├── __init__.py
│   ├── scheduler.py      # Constraint-based timetable generation using OR-Tools
│   └── file_parser.py    # Excel/PDF file parsing and data import
└── migrations/           # Database migrations
```

### Core Models

**User** - Custom authentication model with role-based access
- Role: ADMIN (full CRUD access), VIEWER (read-only)
- Standard Django user fields (username, email, password)

**Department** - Organizational units
- name, code (e.g., "CS", "ENG")

**Course** - Lectures/units to be scheduled
- Code, name, department, year, study mode, class size, hours/week

**Lecturer** - Teaching staff members
- Name, employee ID, email, department, assignable courses

**Room** - Physical venues
- Name, building, capacity, room type (Lecture Hall, Classroom, Seminar)

**TimeSlot** - Available scheduling windows
- Day (Mon-Fri), start/end times
- Unique per day/time combination

**LecturerAvailability** - Constraints on lecturer availability
- Links lecturer to time slot with availability status

**TimetableEntry** - Core output (scheduled lectures)
- Course, Lecturer, Room, TimeSlot
- Unique constraints prevent double-booking
- Can be locked to prevent rescheduling

### Service Layer

**TimetableScheduler** - Constraint Programming Engine
- Uses Google OR-Tools for intelligent scheduling
- Enforces:
  - Each course scheduled exactly once
  - No room double-bookings
  - No lecturer double-bookings
  - Room capacity >= course class size
  - Respects lecturer availability
  - Respects lecturer-course assignments
  
**FileParser** - Data Import
- Parses Excel (.xlsx) and PDF files
- Auto-detects file type
- Creates/updates database entities
- Handles dependency ordering (Departments → Lecturers → Courses)

### Authentication & Permissions

**Custom Permission Class: IsAdminUserOrReadOnly**
- ADMIN users: Full CRUD access
- VIEWER users: Read-only access
- Unauthenticated: No access (except login/register)

**Endpoints:**
- `POST /api/auth/register/` - Create new user (VIEWER role)
- `POST /api/auth/login/` - Authenticate user
- `GET /api/auth/me/` - Get current user info
- `PUT /api/auth/me/update/` - Update profile

### Data Import/Export

**Excel Templates**
- Pre-built template available at `/api/template/`
- Sheets: Departments, Lecturers, Rooms, TimeSlots, Courses
- Validates data and creates entities

**PDF Export**
- Complete timetable or filtered by lecturer/room/course
- Professional formatting with school colors
- Generated on-demand

### Validation

**Built-in Constraints:**
- Room capacity >= course class size
- Lecturer must be assigned to course
- No same-room/lecturer scheduling conflicts
- Time slot validity (start < end)

**Error Handling:**
- Detailed validation error messages
- Non-blocking constraint warnings
- Transaction rollback on critical errors

---

## Frontend Architecture

### Design System

**Color Palette (School Theme)**
- Primary Blue: #1f4788 (Headers, primary buttons)
- Secondary Orange: #FF9500 (Highlights, accents)
- Accent Green: #2ECC71 (Success states, confirmations)
- Neutrals: White, Light Gray (#F5F7FA), Dark Gray (#2C3E50)

**Typography**
- System font stack for optimal readability
- Consistent heading hierarchy (H1-H6)
- 16px base font size with rem scaling

**Components**
- `.card` - White containers with blue left border, hover effects
- `.btn` - Gradient buttons with smooth transitions
- `.table` - Professional tables with gradient headers
- `.badge` - Color-coded status indicators
- `.alert` - Success/danger/warning notifications

### Component Hierarchy

```
App.jsx (Main router)
├── Navbar.jsx (Navigation, auth status, user menu)
├── Dashboard.jsx (Overview, quick stats)
├── DataManager.jsx (CRUD for all entities)
│   ├── DepartmentManager
│   ├── CourseManager
│   ├── LecturerManager
│   ├── RoomManager
│   └── TimeSlotManager
├── TimetableGenerator.jsx (Generate timetable)
├── TimetableViewer.jsx (Display & interact with schedule)
│   ├── TimetableGrid (Weekly calendar view)
│   ├── FilterPanel (By course/lecturer/room)
│   └── ExportPanel (PDF & download)
├── FileUpload.jsx (Import data)
└── Login/Register (Auth flows)
```

### Key Features

**Responsive Design**
- Mobile-first approach
- Works on desktop, tablet, smartphone
- Touch-friendly buttons and navigation
- Collapsible mobile menu

**Accessibility**
- Semantic HTML
- ARIA labels
- Keyboard navigation support
- High contrast colors (WCAG AA compliant)

**Modern UX**
- Smooth animations and transitions
- Loading states with spinners
- Clear error/success messages
- Intuitive form validation
- Drag-and-drop file upload (planned)

---

## API Endpoints Summary

### Authentication
- `POST /api/auth/register/` - Register new user
- `POST /api/auth/login/` - Login
- `GET /api/auth/me/` - Current user info
- `PUT /api/auth/me/update/` - Update profile

### CRUD Operations
- `/api/departments/` - Department management
- `/api/courses/` - Course management
- `/api/lecturers/` - Lecturer management
- `/api/rooms/` - Room management
- `/api/timeslots/` - Time slot management
- `/api/lecturer-availability/` - Availability constraints
- `/api/timetable-entries/` - View/edit schedule entries

### Business Operations
- `POST /api/upload/` - Import Excel/PDF data
- `GET /api/template/` - Download Excel template
- `POST /api/generate/` - Generate timetable
- `GET /api/export-pdf/` - Export schedule as PDF

### Filtered Views
- `/api/courses/{id}/timetable/` - Get course schedule
- `/api/lecturers/{id}/timetable/` - Get lecturer schedule
- `/api/rooms/{id}/timetable/` - Get room schedule

---

## Performance Optimizations

**Backend**
- Database query optimization with `select_related()` and `prefetch_related()`
- Pagination on list endpoints (25 items per page)
- Filtering and search on key fields
- Constraint solver timeout: <2 min for 50+ courses

**Frontend**
- Component code splitting via React Router
- Image optimization and lazy loading
- API request caching where appropriate
- Production build with minification

**Deployment Considerations**
- Docker containers for both services
- Database connection pooling
- Static file CDN caching
- Session timeout: 30 minutes
- CSRF protection enabled

---

## Security Features

**Authentication & Authorization**
- Custom role-based access control (Admin/Viewer)
- Secure password hashing (Django default)
- Session-based authentication
- 30-minute session timeout

**Data Protection**
- CSRF tokens on forms
- SQL injection prevention (ORM)
- XSS protection (Django templates)
- CORS configuration for specific origins

**API Security**
- Rate limiting (can be added)
- Input validation on all endpoints
- Unique constraints on business keys
- Transaction integrity checks

---

## Development Workflow

### Setting Up Locally

**Backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
```

### Database Seeding

```bash
python manage.py shell < seed_data.py
# Or upload sample Excel file via `/api/upload/`
```

### Testing
```bash
python manage.py test
npm run test
```

---

## Future Enhancements

1. **Drag-and-Drop Timetable Editor**
   - Interactive grid interface
   - Real-time conflict detection
   - Visual lock/unlock states

2. **Advanced Scheduling**
   - Multi-objective optimization (minimize gaps, etc.)
   - Room preference constraints
   - Group class scheduling
   - Cross-building transit time

3. **Reporting & Analytics**
   - Lecturer workload analysis
   - Room utilization dashboard
   - Export to ICS/iCal format

4. **Integration Capabilities**
   - SIS integration points
   - Calendar sync (Outlook, Google)
   - Email notifications

5. **Mobile App**
   - Native iOS/Android apps
   - Push notifications for changes
   - Offline viewing

---

## Code Quality

**Standards Followed**
- PEP 8 (Python)
- ESLint/Prettier (JavaScript)
- Django best practices
- REST API conventions

**Documentation**
- Docstrings on all functions/classes
- Inline comments for complex logic
- Type hints where applicable
- Comprehensive README files

**Testing**
- Unit tests for models & services
- Integration tests for APIs
- Component tests for frontend
- Manual testing checklist

---

## Support & Maintenance

- **Bug Reporting:** Create GitHub issues with repro steps
- **Feature Requests:** Use GitHub discussions
- **Security Issues:** Email security@example.com (do not create public issues)
- **Updates:** Check CHANGELOG.md for version history

---

## License

[Your License Here]

---

## Contributors

[List contributors here]

---

*Last Updated: April 2026*
*System Version: 1.0.0*
