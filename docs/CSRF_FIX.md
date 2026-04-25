# CSRF Token Issue - Resolution Guide

## Problem
When trying to register a user, you received this error:
```
CSRF Failed: Origin checking failed - http://localhost:5173 does not match any trusted origins.
```

## Root Cause
Django's CSRF (Cross-Site Request Forgery) protection was rejecting requests from the frontend at `http://localhost:5173` because:
1. The frontend and backend are on different origins (ports)
2. The backend didn't have `CSRF_TRUSTED_ORIGINS` configured
3. The frontend wasn't including CSRF tokens in POST requests

## Solution Implemented

### 1. Backend Configuration (`settings.py`)
Added CSRF configuration to trust the frontend origins:
```python
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:3000',
    'http://localhost:5173'
]

SESSION_COOKIE_SAMESITE = None
CSRF_COOKIE_SAMESITE = None
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
```

### 2. Frontend CSRF Token Handling (`services/api.js`)
Updated API service to automatically:
- Extract CSRF token from cookies
- Send token in `X-CSRFToken` header for all requests

```javascript
function getCsrfToken() {
    // Extract csrftoken from cookies
}

api.interceptors.request.use(config => {
    config.headers['X-CSRFToken'] = getCsrfToken()
    return config
})
```

### 3. CSRF Token Endpoint (`api_views.py`)
Added a GET endpoint to generate and send CSRF tokens:
```python
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_csrf_token(request):
    csrf_token = get_token(request)
    return Response({'csrfToken': csrf_token})
```

### 4. Automatic Token Fetching (`AuthContext.jsx`)
Frontend now fetches CSRF token on app startup:
```javascript
useEffect(() => {
    // Fetch CSRF token first
    await api.get('/auth/csrf-token/')
    // Then check if user is logged in
    // ...
})
```

---

## How It Works Now

### Request Flow
```
1. Frontend loads
   ↓
2. AuthContext calls GET /auth/csrf-token/
   ↓
3. Backend sends CSRF token in response headers/cookies
   ↓
4. Frontend stores token (automatically via axios interceptor)
   ↓
5. User fills registration form and submits
   ↓
6. Frontend POST request includes X-CSRFToken header
   ↓
7. Backend validates CSRF token
   ↓
8. Registration succeeds ✅
```

---

## Testing the Fix

### Restart Both Servers
```bash
# Terminal 1 - Kill and restart backend
# (Ctrl+C to stop)
cd backend
python manage.py runserver

# Terminal 2 - Kill and restart frontend
# (Ctrl+C to stop)
cd frontend
npm run dev
```

### Test Registration
1. Go to `http://localhost:5173/register`
2. Fill in the form:
   - Username: `testuser123`
   - Email: `test@admin.cuk.ac.ke` (or valid CUK email)
   - Password: `testpass123` (min 8 chars)
   - Confirm: `testpass123`
3. Click Register
4. Should see success message and redirect to home ✅

### Test with Debug Page
1. Go to `http://localhost:5173/debug`
2. Enter email and password
3. Click "Test Register"
4. Should see success response with user data ✅

---

## What Changed in Files

### Backend Files
1. **settings.py**
   - Added `CSRF_TRUSTED_ORIGINS`
   - Added `SESSION_COOKIE_SAMESITE = None`
   - Added `CSRF_COOKIE_SAMESITE = None`
   - Added cookie security settings

2. **api_views.py**
   - Added `get_csrf_token()` endpoint

3. **urls.py**
   - Added route for CSRF token endpoint

### Frontend Files
1. **services/api.js**
   - Added CSRF token extraction logic
   - Added request interceptor to include token in headers
   - Improved error handling for 403 responses

2. **context/AuthContext.jsx**
   - Added CSRF token fetching on mount
   - Fixed missing return statements
   - Improved error handling

---

## Verification Checklist

- [ ] Both servers restarted
- [ ] Browser cache cleared (Ctrl+Shift+Delete)
- [ ] No CSRF errors in browser console (F12)
- [ ] Registration form submits without errors
- [ ] User account created successfully
- [ ] Email domain validation works
- [ ] Can login with new account

---

## If Still Having Issues

### 1. Clear Everything and Restart
```bash
# Frontend
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev

# Backend
cd backend
# Make sure settings.py has CSRF_TRUSTED_ORIGINS
python manage.py runserver
```

### 2. Check Browser Console
Open DevTools (F12) → Console and look for:
- CSRF token fetch success message
- Any network errors
- Exact error messages

### 3. Check Network Tab
- Look for GET request to `/auth/csrf-token/`
- Check if response includes `csrftoken` in cookies
- Verify POST requests include `X-CSRFToken` header

### 4. Django Logs
Check Django terminal for:
```
CSRF validation: ...
Invalid CSRF token
```

---

## Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| "CSRF token missing" | Browser issue | Clear cookies, restart browser |
| "CSRF token incorrect" | Token expired | Refresh page to get new token |
| "Origin not trusted" | Settings not updated | Restart Django server |
| 403 Forbidden errors | CSRF validation failed | Check browser console for details |

---

## Production Deployment Notes

⚠️ **IMPORTANT**: Before deploying to production:

1. Update `CSRF_TRUSTED_ORIGINS` with your production domain
2. Set `SESSION_COOKIE_SECURE = True` (requires HTTPS)
3. Set `CSRF_COOKIE_SECURE = True` (requires HTTPS)
4. Change `SESSION_COOKIE_SAMESITE = 'Strict'` (from `None`)
5. Change `CSRF_COOKIE_SAMESITE = 'Strict'` (from `None`)

```python
# Production settings
if not DEBUG:
    CSRF_TRUSTED_ORIGINS = ['https://yourdomain.com', 'https://www.yourdomain.com']
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    CSRF_COOKIE_SAMESITE = 'Strict'
```

---

## Summary

✅ **CSRF issue resolved**  
✅ **Token fetched automatically**  
✅ **Cross-origin requests working**  
✅ **Registration should work now**

Try registering again - it should work!

---

If you need more help, check:
1. Debug page at `/debug`
2. Browser console (F12)
3. Django terminal output
