# Backend Redevelopment TODO

## Task: Simplify backend to Admin-only system

### Steps:
- [x] 1. Update `models.py` - Remove LECTURER and STUDENT roles; keep domain models
- [x] 2. Update `validators.py` - Admin-only email validation
- [x] 3. Update `serializers.py` - Remove is_lecturer/is_student; admin-only registration
- [x] 4. Update `api_views.py` - Remove student/lecturer permissions and endpoints
- [x] 5. Update `urls.py` - Remove lecturer/student-specific routes
- [x] 6. Update `admin.py` - Reflect single role
- [x] 7. Update `seed_default_users.py` - Only admin seed user
- [x] 8. Update `views.py` - Deprecate old views or update permissions
- [x] 9. Fix missing `pdfplumber` dependency in `requirements.txt`
- [x] 10. Fix database settings — MySQL config was incorrectly using sqlite3 engine

