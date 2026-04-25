# Smart Timetable Generator - API Troubleshooting Guide

## Fixed Issues ✅

### 1. Missing Endpoints
- ✅ Added `/api/auth/current-user/` (alias for `/api/auth/me/`)
- ✅ Added `/api/auth/csrf-token/` - CSRF token endpoint
- ✅ Removed CSRF protection from auth endpoints for API usage

### 2. New Auth Endpoints

```
POST /api/auth/register/      - Register new user
POST /api/auth/login/         - Login user
POST /api/auth/logout/        - Logout user
GET  /api/auth/me/            - Get current user
GET  /api/auth/current-user/  - Get current user (alias)
GET  /api/auth/csrf-token/    - Get CSRF token
POST /api/auth/change-password/ - Change password
```

## Testing Login

### Test Data
Create a test user:
```bash
cd backend
python manage.py shell

# In the shell:
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.create_user(
    username='testuser',
    email='test@example.com',
    password='TestPassword123'
)
exit()
```

### Test Login via cURL
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "TestPassword123"
  }'

# OR with email
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123"
  }'
```

### Expected Response
```json
{
  "id": 1,
  "username": "testuser",
  "email": "test@example.com",
  "first_name": "",
  "last_name": "",
  "role": "viewer",
  "school_id": null,
  "is_staff": false,
  "is_active": true,
  "message": "Login successful"
}
```

## Debugging Checklist

### 1. Check User Exists
```bash
python manage.py shell
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.filter(username='testuser').exists()
```

### 2. Verify Password
```bash
user = User.objects.get(username='testuser')
user.check_password('TestPassword123')  # Should return True
```

### 3. Check User is Active
```bash
user.is_active  # Should be True
```

### 4. Test Authentication Directly
```bash
from django.contrib.auth import authenticate
user = authenticate(username='testuser', password='TestPassword123')
print(user)  # Should return the user object, not None
```

### 5. Frontend - Check Console for Errors
Open browser DevTools (F12) → Console tab:
- Check for network errors
- Check if request is being sent
- Verify response status code

### 6. Check Server Logs
Look at terminal where Django runs - it will show:
```
[24/Apr/2026 13:26:43] "POST /api/auth/login/ HTTP/1.1" 200/401/500
```

- **200**: Success
- **401**: Unauthorized (bad credentials)
- **400**: Bad request (missing data)
- **500**: Server error (check Python traceback)

## Frontend Implementation

### Register User
```javascript
const registerUser = async (data) => {
  const response = await api.post('/auth/register/', {
    username: data.username,
    email: data.email,
    password: data.password,
    password_confirm: data.password,
    first_name: data.firstName || '',
    last_name: data.lastName || ''
  });
  return response.data;
};
```

### Login User
```javascript
const loginUser = async (username, password) => {
  const response = await api.post('/auth/login/', {
    username: username,  // or use 'email' field
    password: password
  });
  return response.data;
};
```

### Get Current User
```javascript
const getCurrentUser = async () => {
  const response = await api.get('/auth/current-user/');
  return response.data;
};
```

### Change Password
```javascript
const changePassword = async (oldPassword, newPassword) => {
  const response = await api.post('/auth/change-password/', {
    old_password: oldPassword,
    new_password: newPassword,
    confirm_password: newPassword
  });
  return response.data;
};
```

## Common Issues & Solutions

### Issue: "User with username/email 'xxx' not found"
**Solution**: The user doesn't exist in the database
- Create the user via Django shell or registration endpoint
- Check spelling and case sensitivity

### Issue: "Password is incorrect"
**Solution**: Password doesn't match
- Ensure caps lock is off
- Verify you're using the correct password
- Test with a new user if unsure

### Issue: "User account is disabled"
**Solution**: User's is_active field is False
```bash
user = User.objects.get(username='testuser')
user.is_active = True
user.save()
```

### Issue: CORS errors in frontend
**Solution**: Already configured in settings.py
- Make sure frontend is on http://localhost:5173 or http://localhost:3000
- Backend should be http://localhost:8000

### Issue: "CSRF token missing" or similar
**Solution**: Already exempted for auth endpoints
- If still having issues, restart Django server
- Clear browser cache

## Running the Project

### Terminal 1: Backend
```bash
cd backend
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```

### Terminal 2: Frontend
```bash
cd frontend
npm install  # if not done
npm run dev
```

Then visit: http://localhost:5173

## Database Reset (if needed)

```bash
cd backend
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser --noinput --username admin --email admin@test.local
```

Then create test user via shell as shown above.
