# Registration Issue - Troubleshooting Guide

## Issue Summary

The registration page wasn't accepting user registrations. This was due to:

1. **Syntax Error in Frontend** - Malformed AuthContext with duplicate catch blocks
2. **Error Handling Issues** - Errors weren't being properly caught and displayed
3. **Validation Error Format Mismatch** - Django ValidationError wasn't being properly converted to DRF format

---

## Fixes Applied

### 1. Fixed Syntax Error in AuthContext
- **File**: `frontend/src/context/AuthContext.jsx`
- **Issue**: Duplicate catch blocks causing syntax error
- **Fix**: Completely rewrote the AuthContext with proper error handling for both register and login

### 2. Improved Error Handling in AuthContext
- Enhanced error message extraction to handle multiple error formats:
  - Simple error field: `{ error: "message" }`
  - Field-specific errors: `{ field_name: ["error1", "error2"] }`
  - Nested field errors
- Both `register()` and `login()` functions now properly log errors to console

### 3. Fixed Backend Serializer Validation
- **File**: `backend/timetable_app/serializers.py`
- **Issue**: Django's `ValidationError` wasn't being caught in serializer
- **Fix**: Added try-catch in `validate_email()` method to convert Django's ValidationError to DRF's serializers.ValidationError

---

## Testing Registration

### Method 1: Using Debug Page (Recommended)

1. Navigate to `http://localhost:5173/debug` (or `http://localhost:3000/debug`)
2. Fill in test email and password
3. Click "Test Register"
4. Check the response/error output

### Method 2: Manual Testing via UI

1. Go to `/register` page
2. Fill in form with:
   - **Username**: Any unique username
   - **Email**: Must end with one of:
     - `@admin.cuk.ac.ke` (becomes Timetabler)
     - `@staff.cuk.ac.ke` (becomes Lecturer)
     - `@student.cuk.ac.ke` (becomes Student)
   - **Password**: At least 8 characters
   - **Confirm Password**: Must match password
3. Click Register
4. Check for error messages or redirection to home

### Method 3: Direct API Testing (cURL)

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser123",
    "email": "test@admin.cuk.ac.ke",
    "password": "testpass123",
    "password_confirm": "testpass123",
    "first_name": "Test",
    "last_name": "User"
  }'
```

---

## What to Look For

### Success Response (201 Created)
```json
{
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "username": "testuser123",
    "email": "test@admin.cuk.ac.ke",
    "role": "TIMETABLER",
    "role_display": "Timetabler (Admin)",
    ...
  }
}
```

### Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `username: Username already exists.` | Username taken | Use a different username |
| `email: Email must be from one of the following domains...` | Invalid email domain | Use `@admin.cuk.ac.ke`, `@staff.cuk.ac.ke`, or `@student.cuk.ac.ke` |
| `email: This email is already registered.` | Email already exists | Use a different email or reset with different username |
| `password: Passwords do not match.` | Password confirm doesn't match | Ensure passwords are identical |
| `password: Ensure this field has at least 8 characters.` | Password too short | Use at least 8 characters |

---

## Debugging Steps

### 1. Check Browser Console
Open DevTools (F12) → Console tab and look for:
```javascript
// Should see detailed error logs like:
Registration error: {...}
Login error: {...}
```

### 2. Check Network Tab
- Go to Network tab in DevTools
- Fill the registration form and submit
- Look for POST request to `/api/auth/register/`
- Check:
  - **Status Code**: Should be 201 (success) or 400 (validation error)
  - **Request Body**: Verify all fields are being sent
  - **Response**: Check what error messages are returned

### 3. Check Backend Logs
In your Django terminal, look for:
```
[timestamp] "POST /api/auth/register/ HTTP/1.1" 201 Created
```
or
```
[timestamp] "POST /api/auth/register/ HTTP/1.1" 400 Bad Request
```

### 4. Database Check
Verify the migration was applied:
```bash
cd backend
python manage.py showmigrations timetable_app
```
You should see a checkmark next to `0002_alter_user_role`

---

## Step-by-Step Setup Verification

### Backend Setup
```bash
cd backend

# 1. Install requirements
pip install -r requirements.txt

# 2. Apply migrations
python manage.py migrate

# 3. Test the API endpoint
python manage.py runserver
```

### Frontend Setup
```bash
cd frontend

# 1. Install dependencies
npm install

# 2. Start dev server
npm run dev  # or npm start
```

### CORS Configuration Check
Ensure `CORS_ALLOWED_ORIGINS` in `backend/timetable_project/settings.py` includes your frontend URL:
```python
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',   # npm start
    'http://localhost:5173',   # Vite dev server
]
```

---

## If Still Having Issues

1. **Clear All Data and Restart**
   ```bash
   # Kill running servers (Ctrl+C)
   
   # Backend
   cd backend
   rm db.sqlite3  # Remove database
   python manage.py migrate  # Recreate schema
   python manage.py createsuperuser  # Create test admin
   python manage.py runserver
   
   # Frontend
   cd frontend
   npm cache clean --force
   npm install
   npm run dev
   ```

2. **Check Logs Carefully**
   - Look for any Python/JavaScript syntax errors
   - Check for import errors
   - Verify all required packages are installed

3. **Test with the Debug Page**
   - Use `/debug` route to get detailed error messages
   - Copy exact error responses for troubleshooting

4. **Verify Email Domain**
   - Test with exact domains: `@admin.cuk.ac.ke`, `@staff.cuk.ac.ke`, `@student.cuk.ac.ke`
   - Check for typos (should be `.cuk.ac.ke` not `.cuk.ac.com`)

---

## Files Modified in the Fix

1. **Frontend**:
   - ✅ `frontend/src/context/AuthContext.jsx` - Fixed syntax error
   - ✅ `frontend/src/pages/ApiDebug.jsx` - Added debug page
   - ✅ `frontend/src/App.jsx` - Added debug route

2. **Backend**:
   - ✅ `backend/timetable_app/serializers.py` - Fixed error handling

---

## Next Steps

1. **Test the registration** using the debug page at `/debug`
2. **Create test accounts** for each role
3. **Test login** for each role type
4. **Verify role-based access** by checking if navigation changes
5. **Proceed with further development**

---

## Support

If you still encounter issues:
1. Check the `/debug` page for exact error responses
2. Look at browser console (F12 → Console)
3. Check Django server logs
4. Verify all files were properly updated
5. Clear browser cache if needed (Ctrl+Shift+Delete)
