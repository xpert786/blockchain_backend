# Setup Guide for Blockchain Admin API

## Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

## Installation Steps

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

This will:
- Create the database tables
- Set up JWT token blacklist tables
- Initialize all models (User, Syndicate, KYC)

### 3. Create a Superuser (Admin)
```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin account.

### 4. Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### 5. Run the Development Server
```bash
python manage.py runserver
```

The server will start at: `http://127.0.0.1:8000/`

## Access Points

### Admin Panel
- URL: `http://127.0.0.1:8000/admin/`
- Login with your superuser credentials
- Manage users, syndicates, and KYC records

### API Endpoints
- Base URL: `http://127.0.0.1:8000/api/`
- See `API_DOCUMENTATION.md` for complete API reference

### Key Endpoints:
- **User Registration:** `POST /api/users/register/`
- **User Login:** `POST /api/users/login/`
- **User List:** `GET /api/users/`
- **Syndicate List:** `GET /api/syndicates/`
- **KYC List:** `GET /api/kyc/`

## Testing the API

### 1. Register a User
```bash
curl -X POST http://127.0.0.1:8000/api/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "TestPass123!",
    "password2": "TestPass123!",
    "first_name": "Test",
    "last_name": "User",
    "role": "investor"
  }'
```

### 2. Login
```bash
curl -X POST http://127.0.0.1:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "TestPass123!"
  }'
```

Save the `access` token from the response.

### 3. Access Protected Endpoint
```bash
curl -X GET http://127.0.0.1:8000/api/users/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Troubleshooting

### Issue: "No module named 'rest_framework'"
**Solution:** Install dependencies
```bash
pip install -r requirements.txt
```

### Issue: "Table doesn't exist"
**Solution:** Run migrations
```bash
python manage.py migrate
```

### Issue: "Permission denied" errors
**Solution:** Make sure you're authenticated and using the correct token

### Issue: Admin page 404 error
**Solution:** The admin is properly configured now. Make sure migrations are run:
```bash
python manage.py migrate
python manage.py collectstatic
```

## Development Notes

### JWT Token Configuration
- Access tokens expire after 5 hours
- Refresh tokens expire after 7 days
- Tokens are automatically blacklisted on logout

### User Roles
- `admin`: Full access to all features
- `syndicate_manager`: Can create and manage syndicates
- `investor`: Can view syndicates and submit KYC

### File Uploads
For file uploads (syndicate logos, KYC documents):
1. Configure `MEDIA_ROOT` and `MEDIA_URL` in settings
2. Use multipart/form-data content type
3. Files will be stored in the media directory

## Production Deployment

Before deploying to production:

1. **Change SECRET_KEY** in settings.py
2. **Set DEBUG = False**
3. **Configure ALLOWED_HOSTS**
4. **Use a production database** (PostgreSQL recommended)
5. **Set up HTTPS**
6. **Configure CORS** if using a separate frontend
7. **Use environment variables** for sensitive data
8. **Set up proper media file handling**
9. **Configure email backend** for password resets
10. **Set up logging**

Example production settings:
```python
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

# Use PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_db_name',
        'USER': 'your_db_user',
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# HTTPS settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

## Next Steps

1. Review the API documentation in `API_DOCUMENTATION.md`
2. Test all endpoints using Postman or cURL
3. Customize the models if needed
4. Add additional validation rules
5. Implement email notifications
6. Add more custom endpoints as required

## Support

For questions or issues, refer to:
- Django documentation: https://docs.djangoproject.com/
- Django REST Framework: https://www.django-rest-framework.org/
- SimpleJWT: https://django-rest-framework-simplejwt.readthedocs.io/

---

Happy coding! 🚀


