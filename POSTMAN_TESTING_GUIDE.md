# Postman Testing Guide - Syndicate Image Upload API

## 🚀 Quick Start Testing

### Step 1: Import Postman Collection

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
   - Click environment dropdown (top right)
   - Select "Syndicate API Environment"

### Step 2: Test Authentication

#### **Register a New User:**
1. Go to **"Authentication" → "Register User"**
2. Click **"Send"**
3. **Expected Response (201):**
```json
{
    "message": "User registered successfully",
    "user_id": 27,
    "username": "testuser123",
    "email": "test@example.com",
    "tokens": {
        "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
}
```

4. **Copy the `access` token** from the response

#### **Set Access Token:**
1. Click environment dropdown → **"Edit"**
2. Find `access_token` variable
3. Paste your token as the value
4. Click **"Save"**

### Step 3: Create a Syndicate

#### **Create Syndicate:**
1. Go to **"Syndicate Management" → "Create Syndicate"**
2. Click **"Send"**
3. **Expected Response (201):**
```json
{
    "id": 2,
    "name": "Tech Ventures Syndicate",
    "description": "A syndicate focused on early-stage technology investments",
    "manager": 27,
    "time_of_register": "2025-01-16T15:30:00Z"
}
```

4. **Copy the syndicate `id`** from the response

#### **Set Syndicate ID:**
1. Edit environment variables
2. Set `syndicate_id` to your syndicate ID
3. Save

### Step 4: Test Image Upload

#### **Upload a Logo:**
1. Go to **"Image Upload" → "Upload Logo"**
2. In the **Body** tab, find the `image` field
3. Click **"Select Files"** and choose a logo image
4. Click **"Send"**
5. **Expected Response (201):**
```json
{
    "success": true,
    "message": "Image uploaded successfully",
    "image": {
        "id": 1,
        "image_type": "logo",
        "title": "Company Logo",
        "is_primary": true,
        "image_url": "/media/syndicate_images/2/logo/logo.png"
    }
}
```

#### **Upload a Banner:**
1. Go to **"Image Upload" → "Upload Banner"**
2. Select a banner image file
3. Click **"Send"**

#### **Upload Gallery Images:**
1. Go to **"Image Upload" → "Upload Gallery Image"**
2. Select gallery images
3. Click **"Send"**

### Step 5: Test Image Management

#### **Get All Images:**
1. Go to **"Image Management" → "Get All Images"**
2. Click **"Send"**
3. **Expected Response (200):**
```json
{
    "syndicate_id": 2,
    "syndicate_name": "Tech Ventures Syndicate",
    "images": [
        {
            "id": 1,
            "image_type": "logo",
            "title": "Company Logo",
            "is_primary": true,
            "image_url": "/media/syndicate_images/2/logo/logo.png"
        }
    ],
    "total_count": 1
}
```

#### **Get Images by Type:**
1. Go to **"Image Management" → "Get Images by Type"**
2. The query parameter `image_type=logo` is already set
3. Click **"Send"**

#### **Set Primary Image:**
1. Go to **"Image Management" → "Set Primary Image"**
2. In the request body, set `image_id` to an existing image ID
3. Click **"Send"**

#### **Update Image Info:**
1. Go to **"Image Management" → "Update Image Info"**
2. Update the JSON body with new information
3. Click **"Send"**

#### **Delete Image:**
1. Go to **"Image Management" → "Delete Image"**
2. Set `image_id` in the request body
3. Click **"Send"**

## 🧪 Complete Testing Workflow

### **Test Scenario 1: Basic Image Upload**

1. **Register User** → Get access token
2. **Create Syndicate** → Get syndicate ID
3. **Upload Logo** → Upload company logo
4. **Upload Banner** → Upload banner image
5. **Get All Images** → Verify uploads

### **Test Scenario 2: Image Management**

1. **Upload Multiple Gallery Images** → Upload 3-4 gallery images
2. **Get Images by Type** → Filter by `gallery`
3. **Set Primary Image** → Set one gallery image as primary
4. **Update Image Info** → Update titles and descriptions
5. **Delete Image** → Remove one image

### **Test Scenario 3: Single API Call**

1. **Create Complete Syndicate** → Use single API with logo upload
2. **Get Syndicate Details** → Verify complete data

## 📊 Expected Responses

### **Successful Image Upload (201):**
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
        "uploaded_at": "2025-01-16T15:30:00Z",
        "file_size": 1024000,
        "mime_type": "image/png",
        "image_url": "/media/syndicate_images/2/logo/logo.png"
    }
}
```

### **Get Images Response (200):**
```json
{
    "syndicate_id": 2,
    "syndicate_name": "Tech Ventures Syndicate",
    "images": [
        {
            "id": 1,
            "image_type": "logo",
            "title": "Company Logo",
            "description": "Main company logo",
            "alt_text": "Company logo image",
            "is_primary": true,
            "uploaded_at": "2025-01-16T15:30:00Z",
            "file_size": 1024000,
            "mime_type": "image/png",
            "image_url": "/media/syndicate_images/2/logo/logo.png"
        }
    ],
    "total_count": 1
}
```

### **Error Response (400):**
```json
{
    "error": "Image file is required"
}
```

## 🔍 Testing Checklist

### **Authentication Tests:**
- [ ] Register user successfully
- [ ] Login user successfully
- [ ] Access token works for authenticated requests
- [ ] Unauthorized access returns 401

### **Syndicate Tests:**
- [ ] Create syndicate successfully
- [ ] Get syndicates list
- [ ] Only manager can access their syndicates

### **Image Upload Tests:**
- [ ] Upload logo image
- [ ] Upload banner image
- [ ] Upload gallery images
- [ ] Upload team photos
- [ ] Handle different image formats (JPG, PNG, GIF)
- [ ] Validate file size limits
- [ ] Set primary images correctly

### **Image Management Tests:**
- [ ] Get all images for syndicate
- [ ] Filter images by type
- [ ] Set primary image
- [ ] Update image information
- [ ] Delete images
- [ ] Verify file cleanup on deletion

### **Error Handling Tests:**
- [ ] Missing required fields
- [ ] Invalid file formats
- [ ] File size too large
- [ ] Unauthorized access
- [ ] Invalid syndicate ID
- [ ] Invalid image ID

## 🐛 Common Issues & Solutions

### **Issue 1: 401 Unauthorized**
**Solution:** Check if access token is set correctly in environment variables

### **Issue 2: 404 Not Found**
**Solution:** Verify syndicate_id is correct and you're the manager

### **Issue 3: File Upload Fails**
**Solution:** 
- Check file size (max 10MB)
- Verify file format (JPG, PNG, GIF, etc.)
- Ensure file path is correct

### **Issue 4: CORS Errors**
**Solution:** Server should be running on `192.168.0.146:8000`

## 📝 Test Data Examples

### **Sample Image Files to Test:**
- **Logo:** 200x200px PNG file
- **Banner:** 1200x400px JPG file
- **Gallery:** Various sized images
- **Team Photo:** Group photo JPG

### **Test Image Information:**
```json
{
    "title": "Test Company Logo",
    "description": "This is a test logo upload",
    "alt_text": "Company logo for testing",
    "image_type": "logo"
}
```

## 🎯 Performance Testing

### **Upload Multiple Images:**
1. Upload 10+ images of different types
2. Check response times
3. Verify all images are stored correctly
4. Test getting all images

### **Large File Testing:**
1. Upload images close to 10MB limit
2. Verify upload success
3. Check file storage

## 📞 Troubleshooting

If tests fail:
1. Check server logs
2. Verify database migrations are applied
3. Check file permissions in media folder
4. Verify CORS settings
5. Test with simple requests first

## 🏆 Success Criteria

All tests pass when:
- [ ] User registration/login works
- [ ] Syndicate creation works
- [ ] Image uploads work for all types
- [ ] Image management operations work
- [ ] Error handling works correctly
- [ ] File storage and cleanup works
- [ ] CORS is properly configured
