# Postman Setup Guide for Syndicate Image Upload API

## 📋 Quick Setup

### 1. Import Collection and Environment

1. **Open Postman**
2. **Import Collection:**
   - Click "Import" button
   - Select `Syndicate_Image_Upload_API.postman_collection.json`
   - Click "Import"

3. **Import Environment:**
   - Click "Import" button
   - Select `Syndicate_API_Environment.postman_environment.json`
   - Click "Import"

4. **Select Environment:**
   - Click the environment dropdown (top right)
   - Select "Syndicate API Environment"

### 2. Get Authentication Token

1. **Register a User:**
   - Go to "Authentication" → "Register User"
   - Click "Send"
   - Copy the `access` token from the response

2. **Set Access Token:**
   - Click the environment dropdown
   - Click "Edit" next to "Syndicate API Environment"
   - Set `access_token` value to your token
   - Click "Save"

### 3. Create a Syndicate

1. **Create Syndicate:**
   - Go to "Syndicate Management" → "Create Syndicate"
   - Click "Send"
   - Copy the syndicate `id` from the response

2. **Set Syndicate ID:**
   - Edit environment variables
   - Set `syndicate_id` to your syndicate ID
   - Save

## 🚀 Using the API

### Upload Images

1. **Upload Logo:**
   - Go to "Image Upload" → "Upload Logo"
   - In the Body tab, click "Select Files" next to the image field
   - Choose your logo image file
   - Click "Send"

2. **Upload Banner:**
   - Go to "Image Upload" → "Upload Banner"
   - Select your banner image
   - Click "Send"

3. **Upload Gallery Images:**
   - Go to "Image Upload" → "Upload Gallery Image"
   - Select your gallery image
   - Click "Send"

### Manage Images

1. **View All Images:**
   - Go to "Image Management" → "Get All Images"
   - Click "Send"

2. **Set Primary Image:**
   - Go to "Image Management" → "Set Primary Image"
   - Set `image_id` in the request body
   - Click "Send"

3. **Update Image Info:**
   - Go to "Image Management" → "Update Image Info"
   - Update the JSON body with new information
   - Click "Send"

4. **Delete Image:**
   - Go to "Image Management" → "Delete Image"
   - Set `image_id` in the request body
   - Click "Send"

## 📁 Collection Structure

### **Authentication**
- Register User
- Login User

### **Syndicate Management**
- Create Syndicate
- Get Syndicates

### **Image Upload**
- Upload Logo
- Upload Banner
- Upload Gallery Image
- Upload Team Photo

### **Image Management**
- Get All Images
- Get Images by Type
- Set Primary Image
- Update Image Info
- Delete Image

### **Single Syndicate API**
- Create Complete Syndicate
- Get Syndicate Details

## 🔧 Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `base_url` | API base URL | `http://192.168.0.146:8000` |
| `access_token` | JWT access token | `eyJhbGciOiJIUzI1NiIs...` |
| `refresh_token` | JWT refresh token | `eyJhbGciOiJIUzI1NiIs...` |
| `syndicate_id` | Current syndicate ID | `1` |
| `image_id` | Current image ID | `1` |
| `user_id` | Current user ID | `1` |
| `username` | Username for auth | `testuser123` |
| `email` | Email for auth | `test@example.com` |
| `password` | Password for auth | `testpass123` |

## 📝 Example Workflow

### Complete Syndicate Creation with Images:

1. **Register/Login** → Get access token
2. **Create Syndicate** → Get syndicate ID
3. **Upload Logo** → Set as primary logo
4. **Upload Banner** → Set as primary banner
5. **Upload Gallery Images** → Add multiple gallery images
6. **Upload Team Photo** → Add team photos
7. **Get All Images** → View all uploaded images
8. **Set Primary Images** → Choose primary images for each type

### Single API Call (Alternative):

1. **Register/Login** → Get access token
2. **Create Complete Syndicate** → Upload everything in one call
3. **Get Syndicate Details** → View complete syndicate with all data

## 🎯 Image Types Available

- **logo** - Company/Syndicate logo
- **banner** - Banner image
- **gallery** - General gallery images
- **document** - Document images
- **certificate** - Certificate images
- **team_photo** - Team photos
- **office_photo** - Office photos
- **other** - Other images

## 📊 Response Examples

### Successful Image Upload:
```json
{
    "success": true,
    "message": "Image uploaded successfully",
    "image": {
        "id": 1,
        "image_type": "logo",
        "title": "Company Logo",
        "description": "Main company logo",
        "alt_text": "Company logo image",
        "is_primary": true,
        "uploaded_at": "2025-01-16T12:00:00Z",
        "file_size": 1024000,
        "mime_type": "image/png",
        "image_url": "/media/syndicate_images/1/logo/logo.png"
    }
}
```

### Get Images Response:
```json
{
    "syndicate_id": 1,
    "syndicate_name": "Tech Ventures Syndicate",
    "images": [
        {
            "id": 1,
            "image_type": "logo",
            "title": "Company Logo",
            "is_primary": true,
            "image_url": "/media/syndicate_images/1/logo/logo.png"
        }
    ],
    "total_count": 1
}
```

## ⚠️ Important Notes

1. **Authentication Required:** All endpoints require a valid JWT token
2. **File Size Limit:** Maximum 10MB per image
3. **Supported Formats:** JPG, PNG, GIF, BMP, WEBP
4. **Primary Images:** Only one primary image per type
5. **Access Control:** Only syndicate managers can upload/manage images
6. **CORS Enabled:** Frontend integration supported

## 🔍 Troubleshooting

### Common Issues:

1. **401 Unauthorized:**
   - Check if access token is set correctly
   - Token might be expired, try logging in again

2. **404 Not Found:**
   - Check if syndicate_id is correct
   - Ensure you're the manager of the syndicate

3. **400 Bad Request:**
   - Check if all required fields are provided
   - Verify file format and size

4. **CORS Errors:**
   - Ensure server is running on correct IP
   - Check CORS configuration

## 📞 Support

If you encounter any issues:
1. Check the server logs
2. Verify environment variables
3. Test with simple requests first
4. Check file permissions and paths
