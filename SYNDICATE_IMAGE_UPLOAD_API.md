# Syndicate Image Upload API

This API allows you to upload, manage, and organize images for syndicates.

## Base URL
```
http://192.168.0.146:8000/api/syndicate-images/
```

## Image Upload
**POST** `/api/syndicate-images/upload_image/`

**Content-Type:** `multipart/form-data`

### Form Data Fields

#### **Required Fields:**
```
syndicate_id: 1                    # ID of the syndicate
image: [FILE]                      # Image file (JPG, PNG, GIF, etc.)
```

#### **Optional Fields:**
```
image_type: "logo"                 # Type of image (see types below)
title: "Company Logo"              # Title for the image
description: "Main company logo"   # Description
alt_text: "Company logo image"     # Alt text for accessibility
is_primary: "true"                 # Set as primary image for this type
```

### Image Types Available:
- `logo` - Company/Syndicate logo
- `banner` - Banner image
- `gallery` - General gallery images
- `document` - Document images
- `certificate` - Certificate images
- `team_photo` - Team photos
- `office_photo` - Office photos
- `other` - Other images

### Example cURL Request:
```bash
curl --location 'http://192.168.0.146:8000/api/syndicate-images/upload_image/' \
--header 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
--form 'syndicate_id=1' \
--form 'image=@/path/to/logo.png' \
--form 'image_type=logo' \
--form 'title=Company Logo' \
--form 'description=Main company logo' \
--form 'alt_text=Company logo image' \
--form 'is_primary=true'
```

### Success Response (201 Created):
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

## Get Syndicate Images
**GET** `/api/syndicate-images/get_syndicate_images/?syndicate_id=1&image_type=logo`

### Query Parameters:
- `syndicate_id` (required) - ID of the syndicate
- `image_type` (optional) - Filter by image type

### Example:
```bash
curl --location 'http://192.168.0.146:8000/api/syndicate-images/get_syndicate_images/?syndicate_id=1&image_type=logo' \
--header 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

### Response:
```json
{
    "syndicate_id": 1,
    "syndicate_name": "Tech Ventures Syndicate",
    "images": [
        {
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
    ],
    "total_count": 1
}
```

## Set Primary Image
**POST** `/api/syndicate-images/set_primary_image/`

### Request Body:
```json
{
    "image_id": 1
}
```

### Example:
```bash
curl --location 'http://192.168.0.146:8000/api/syndicate-images/set_primary_image/' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
--data '{
    "image_id": 1
}'
```

### Response:
```json
{
    "success": true,
    "message": "Image set as primary logo",
    "image": {
        "id": 1,
        "image_type": "logo",
        "title": "Company Logo",
        "is_primary": true,
        "image_url": "/media/syndicate_images/1/logo/logo.png"
    }
}
```

## Update Image Information
**POST** `/api/syndicate-images/update_image_info/`

### Request Body:
```json
{
    "image_id": 1,
    "title": "Updated Logo Title",
    "description": "Updated description",
    "alt_text": "Updated alt text"
}
```

### Example:
```bash
curl --location 'http://192.168.0.146:8000/api/syndicate-images/update_image_info/' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
--data '{
    "image_id": 1,
    "title": "Updated Logo Title",
    "description": "Updated description",
    "alt_text": "Updated alt text"
}'
```

## Delete Image
**DELETE** `/api/syndicate-images/delete_image/`

### Request Body:
```json
{
    "image_id": 1
}
```

### Example:
```bash
curl --location 'http://192.168.0.146:8000/api/syndicate-images/delete_image/' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
--data '{
    "image_id": 1
}'
```

### Response:
```json
{
    "success": true,
    "message": "Image \"Company Logo\" deleted successfully"
}
```

## Frontend Integration Examples

### **JavaScript with FormData:**
```javascript
const uploadImage = async (syndicateId, imageFile, imageType = 'gallery') => {
    const formData = new FormData();
    formData.append('syndicate_id', syndicateId);
    formData.append('image', imageFile);
    formData.append('image_type', imageType);
    formData.append('title', 'My Image');
    formData.append('description', 'Image description');
    formData.append('alt_text', 'Alt text for accessibility');
    formData.append('is_primary', 'false');
    
    try {
        const response = await fetch('http://192.168.0.146:8000/api/syndicate-images/upload_image/', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${accessToken}`
            },
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            console.log('Image uploaded:', result);
            return result.image;
        } else {
            console.error('Upload failed:', result.error);
            throw new Error(result.error);
        }
    } catch (error) {
        console.error('Network error:', error);
        throw error;
    }
};

// Usage
const fileInput = document.getElementById('imageInput');
const file = fileInput.files[0];
uploadImage(1, file, 'logo').then(image => {
    console.log('Uploaded image:', image);
});
```

### **React Example:**
```jsx
import React, { useState } from 'react';

const ImageUpload = ({ syndicateId }) => {
    const [uploading, setUploading] = useState(false);
    const [images, setImages] = useState([]);
    
    const handleImageUpload = async (event) => {
        const file = event.target.files[0];
        if (!file) return;
        
        setUploading(true);
        
        const formData = new FormData();
        formData.append('syndicate_id', syndicateId);
        formData.append('image', file);
        formData.append('image_type', 'gallery');
        formData.append('title', file.name);
        
        try {
            const response = await fetch('/api/syndicate-images/upload_image/', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
                },
                body: formData
            });
            
            const result = await response.json();
            
            if (response.ok) {
                setImages([...images, result.image]);
                alert('Image uploaded successfully!');
            } else {
                alert('Upload failed: ' + result.error);
            }
        } catch (error) {
            alert('Network error: ' + error.message);
        } finally {
            setUploading(false);
        }
    };
    
    const fetchImages = async () => {
        try {
            const response = await fetch(`/api/syndicate-images/get_syndicate_images/?syndicate_id=${syndicateId}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
                }
            });
            
            const result = await response.json();
            
            if (response.ok) {
                setImages(result.images);
            }
        } catch (error) {
            console.error('Error fetching images:', error);
        }
    };
    
    return (
        <div>
            <input 
                type="file" 
                accept="image/*" 
                onChange={handleImageUpload}
                disabled={uploading}
            />
            {uploading && <p>Uploading...</p>}
            
            <div className="image-gallery">
                {images.map(image => (
                    <div key={image.id} className="image-item">
                        <img 
                            src={image.image_url} 
                            alt={image.alt_text || image.title}
                            style={{ width: '200px', height: '200px', objectFit: 'cover' }}
                        />
                        <h4>{image.title}</h4>
                        <p>{image.description}</p>
                        {image.is_primary && <span className="primary-badge">Primary</span>}
                    </div>
                ))}
            </div>
        </div>
    );
};
```

## File Storage

### **Storage Location:**
Images are stored in: `media/syndicate_images/{syndicate_id}/{image_type}/{filename}`

### **Supported Formats:**
- **Images:** JPG, JPEG, PNG, GIF, BMP, WEBP
- **Maximum File Size:** 10MB per image
- **Recommended Dimensions:** 
  - Logo: 200x200px to 500x500px
  - Banner: 1200x400px to 1920x600px
  - Gallery: Any size up to 10MB

### **File Organization:**
```
media/
└── syndicate_images/
    └── 1/                    # Syndicate ID
        ├── logo/
        │   └── company_logo.png
        ├── banner/
        │   └── main_banner.jpg
        ├── gallery/
        │   ├── office_1.jpg
        │   └── office_2.jpg
        └── team_photo/
            └── team_2024.jpg
```

## Error Handling

### **Common Errors:**
- **400 Bad Request:** Missing required fields or invalid data
- **401 Unauthorized:** Invalid or missing authentication token
- **404 Not Found:** Syndicate or image not found
- **413 Payload Too Large:** File size exceeds limit

### **Error Response Format:**
```json
{
    "error": "Detailed error message"
}
```

## Features

✅ **Multiple Image Types** - Logo, banner, gallery, documents, etc.  
✅ **Primary Image Selection** - Set one image as primary per type  
✅ **Image Metadata** - Title, description, alt text support  
✅ **File Management** - Automatic file organization and cleanup  
✅ **Access Control** - Only syndicate managers can upload/manage  
✅ **File Validation** - Size and format checking  
✅ **RESTful API** - Standard HTTP methods and responses  

## Notes

- All endpoints require authentication
- Only syndicate managers can upload/manage images
- Primary images are automatically managed (only one per type)
- Files are automatically deleted when images are removed
- Image URLs are relative to the media root
- CORS is configured for frontend integration
