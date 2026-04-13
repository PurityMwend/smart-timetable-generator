# Smart Timetable Generator - Authentication & Permissions Implementation

## Overview

A complete role-based authentication and permissions system has been implemented for the Smart Timetable Generator. Users are automatically assigned roles based on their email domain, and permissions are enforced at both API and frontend levels.

---

## Email Domain-Based Role Assignment

### Role Mapping

| Email Domain | Role | Privileges |
|---|---|---|
| `@admin.cuk.ac.ke` | **Timetabler** | Superuser - Full CRUD access, can manage all timetable operations |
| `@staff.cuk.ac.ke` | **Lecturer** | Read timetables, manage own availability, but cannot edit timetables |
| `@student.cuk.ac.ke` | **Student** | Read-only access to timetables |

---

## Backend Implementation

### 1. **User Model Updates** (`models.py`)

```python
class Role(models.TextChoices):
    TIMETABLER = 'TIMETABLER', 'Timetabler (Admin)'
    LECTURER = 'LECTURER', 'Lecturer'
    STUDENT = 'STUDENT', 'Student'

# Helper properties
@property
def is_timetabler(self):
    return self.role == self.Role.TIMETABLER

@property
def is_lecturer(self):
    return self.role == self.Role.LECTURER

@property
def is_student(self):
    return self.role == self.Role.STUDENT
```

### 2. **Email Validators** (`validators.py`)

- `get_user_role_from_email(email)` - Determines role from email domain
- `validate_cuk_email(email)` - Ensures email is from allowed CUK domain
- `validate_email_not_registered(email)` - Prevents duplicate registrations

### 3. **Authentication Serializers** (`serializers.py`)

- `UserSerializer` - Returns user data with role information
- `RegisterSerializer` - Handles registration with email validation and role assignment
- `LoginSerializer` - Validates credentials and authenticates user

### 4. **Custom Permission Classes** (`api_views.py`)

```python
IsTimetablerUser              # Only timetablers
IsLecturerUser                # Lecturers and timetablers
IsTimetablerOrReadOnly        # Timetablers can edit, others read-only
CanEditTimetable              # Only timetablers can edit timetables
```

### 5. **Authentication Endpoints** (`api_views.py`)

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/auth/register/` | POST | User registration |
| `/api/auth/login/` | POST | User login |
| `/api/auth/logout/` | POST | User logout |
| `/api/auth/current-user/` | GET | Get current user info |
| `/api/auth/profile/` | PUT/PATCH | Update user profile |

### 6. **Database Migration** (`0002_alter_user_role.py`)

Migration file created to update the User model's role field from ADMIN/VIEWER to TIMETABLER/LECTURER/STUDENT.

---

## Frontend Implementation

### 1. **Authentication Context** (`context/AuthContext.jsx`)

Global authentication state management with:
- `user` - Current user object
- `isAuthenticated` - Authentication status
- `isTimetabler`, `isLecturer`, `isStudent` - Role checks
- Methods: `login()`, `register()`, `logout()`, `updateProfile()`

### 2. **Protected Routes** (`components/PrivateRoute.jsx`)

Route protection component that:
- Checks if user is authenticated
- Validates role-based access (`requiredRole` prop)
- Redirects to login if not authenticated
- Redirects to home if insufficient permissions

### 3. **Authentication Pages**

#### Login Page (`pages/Login.jsx`)
- Username/password login form
- Email domain information display
- Error handling

#### Register Page (`pages/Register.jsx`)
- Registration form with:
  - Username, email, password, first/last name
  - Email validation (must be from CUK domain)
  - Password confirmation
  - Role information display based on email

### 4. **Updated Navbar** (`components/Navbar.jsx`)

Features:
- Shows user avatar and name when logged in
- Displays current user role
- User dropdown menu with profile, settings, logout
- Conditional navigation based on role:
  - Timetablers see: Dashboard, Data Manager, Generate, Timetable
  - Lecturers see: Dashboard, Timetable
  - Students see: Dashboard, Timetable
- Login/Register links for unauthenticated users

### 5. **API Service** (`services/api.js`)

Axios instance with:
- Automatic error handling (401 redirects to login)
- Session-based authentication
- Credentials included in requests

---

## Usage

### For Running the Application

#### 1. **Apply Database Migration**

```bash
cd backend
python manage.py migrate
```

#### 2. **Start Django Server**

```bash
python manage.py runserver
```

#### 3. **Start React Development Server**

```bash
cd frontend
npm install
npm run dev
```

### For Testing

#### Create Test Users

```bash
# Via Django shell
python manage.py shell

from timetable_app.models import User

# Create a timetabler
User.objects.create_user(
    username='admin_user',
    email='admin@admin.cuk.ac.ke',
    password='securepass123',
    role='TIMETABLER'
)

# Create a lecturer
User.objects.create_user(
    username='lecturer_user',
    email='lecturer@staff.cuk.ac.ke',
    password='securepass123',
    role='LECTURER'
)

# Create a student
User.objects.create_user(
    username='student_user',
    email='student@student.cuk.ac.ke',
    password='securepass123',
    role='STUDENT'
)
```

#### Test Registration via UI

1. Navigate to `/register`
2. Enter credentials with valid CUK email domain
3. User role automatically assigned based on email domain
4. Login with created credentials at `/login`

#### Test Access Control

- **Timetablers** can access all features
- **Lecturers** cannot see Data Manager or Generate pages
- **Students** can only view timetables (read-only)

---

## Access Control Examples

### API Level

```python
# Only timetablers can create/edit
@permission_classes([permissions.IsAuthenticated, CanEditTimetable])
def create_timetable_entry(request):
    # ...

# Lecturers and timetablers can view
@permission_classes([permissions.IsAuthenticated, IsLecturerUser])
def view_timetable(request):
    # ...

# Everyone authenticated can read
@permission_classes([permissions.IsAuthenticated])
def list_timetables(request):
    # ...
```

### Frontend Level

```jsx
{/* Only timetablers can access */}
<Route
    path="/generate"
    element={
        <PrivateRoute requiredRole="timetabler">
            <TimetableGenerator />
        </PrivateRoute>
    }
/>

{/* Lecturers and timetablers can access */}
<Route
    path="/data"
    element={
        <PrivateRoute requiredRole="lecturer">
            <DataManager />
        </PrivateRoute>
    }
/>

{/* All authenticated users can access */}
<Route
    path="/view"
    element={
        <PrivateRoute>
            <TimetableViewer />
        </PrivateRoute>
    }
/>
```

---

## Security Features

1. **Email Domain Validation**
   - Only CUK email domains allowed
   - Automatic role assignment based on domain
   - Prevents registration with external emails

2. **Password Security**
   - Minimum 8 characters
   - Django's built-in password validators
   - Current password verification for changes

3. **Session-Based Authentication**
   - Secure session cookies
   - CSRF protection
   - Credentials included in all requests

4. **Role-Based Access Control**
   - Two-level enforcement (API + Frontend)
   - Endpoint-level permissions
   - Route-level guards

5. **Email Immutability**
   - Users cannot change email (prevents role escalation)
   - Email domain determines role permanently

---

## Files Modified/Created

### Backend Files
- ✅ `models.py` - Updated User model with 3 roles
- ✅ `validators.py` - Added email domain validators
- ✅ `serializers.py` - Updated serializers and added auth serializers
- ✅ `api_views.py` - Added custom permissions and updated endpoints
- ✅ `urls.py` - Added logout endpoint
- ✅ `migrations/0002_alter_user_role.py` - Database migration

### Frontend Files
- ✅ `context/AuthContext.jsx` - Authentication context
- ✅ `components/PrivateRoute.jsx` - Protected routes
- ✅ `pages/Login.jsx` - Login page
- ✅ `pages/Register.jsx` - Registration page
- ✅ `pages/Auth.css` - Authentication pages styling
- ✅ `components/Navbar.jsx` - Updated navbar with user menu
- ✅ `components/Navbar.css` - Updated navbar styling
- ✅ `services/api.js` - Updated API service
- ✅ `App.jsx` - Updated with auth integration

---

## Future Enhancements

1. **Email Verification** - Verify CUK email before account activation
2. **OAuth Integration** - SSO via institution's OAuth provider
3. **Permission Granularity** - More fine-grained permissions per resource
4. **Password Reset** - Email-based password recovery
5. **Audit Logging** - Track all user actions
6. **Token-Based Auth** - JWT tokens for mobile app support
7. **Two-Factor Authentication** - Additional security layer
8. **Admin Dashboard** - User management interface for timetablers

---

## Troubleshooting

### "Invalid email domain" error during registration
- Ensure email ends with `@admin.cuk.ac.ke`, `@staff.cuk.ac.ke`, or `@student.cuk.ac.ke`

### "Access Denied" when navigating to restricted pages
- Verify your account role (check navbar user dropdown)
- Log out and log back in if role was just changed

### Migration errors
```bash
# Reset migrations (for development only)
python manage.py migrate timetable_app zero
python manage.py migrate
```

### Frontend not reflecting auth changes
- Clear browser cache and cookies
- Verify API requests include `withCredentials: true`

---

## Support & Questions

For issues or questions regarding the authentication system:
1. Check the logs in Django console
2. Review browser network tab in DevTools
3. Verify database migration was applied
4. Ensure frontend and backend are properly connected
