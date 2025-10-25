# Single Syndicate Creation API

This API allows you to create a complete syndicate with all data and documents in a single API call.

## Base URL
```
http://192.168.0.146:8000/api/single-syndicate/
```

## Create Syndicate
**POST** `/api/single-syndicate/create_syndicate/`

**Content-Type:** `multipart/form-data`

### Form Data Fields

#### **Basic Information (Required)**
```
name: "Tech Ventures Syndicate"                    # Required
description: "A syndicate focused on early-stage technology investments"
accredited: "Yes"                                  # Yes/No
firm_name: "Tech Ventures LLC"
lp_network: "Angel investors, VCs, Family offices"
enable_lp_network: "Yes"                           # Yes/No
```

#### **Sectors and Geographies**
```
sector_ids: "1,2,3"                               # Comma-separated IDs or JSON array
geography_ids: "1,2,4"                            # Comma-separated IDs or JSON array
```

#### **Team Members (JSON Array)**
```
team_members: [
    {
        "name": "John Manager",
        "email": "john@techventures.com",
        "role": "Managing Partner",
        "description": "Experienced investor with 10+ years",
        "linkedin_profile": "https://linkedin.com/in/johnmanager"
    },
    {
        "name": "Sarah Smith",
        "email": "sarah@techventures.com",
        "role": "Investment Analyst",
        "description": "Specializes in AI and blockchain investments"
    }
]
```

#### **Beneficiaries (JSON Array)**
```
beneficiaries: [
    {
        "name": "John Manager",
        "email": "john@techventures.com",
        "relationship": "Owner",
        "ownership_percentage": 100.00
    }
]
```

#### **Compliance & Attestation**
```
Risk_Regulatory_Attestation: "This syndicate complies with all SEC regulations..."
jurisdictional_requirements: "United States, Canada, United Kingdom"
additional_compliance_policies: "KYC/AML policies enforced..."
risk_regulatory_attestation: "true"               # true/false
jurisdictional_requirements_check: "true"         # true/false
additional_compliance_policies_check: "true"      # true/false
self_knowledge_aml_policies: "true"               # true/false
is_regulated_entity: "true"                       # true/false
is_ml_tf_risk: "false"                            # true/false
attestation_text: "I attest that all information is accurate..."
```

#### **Document Uploads (Files)**
```
syndicate_logo: [FILE]                            # Image file
company_certificate: [FILE]                       # PDF/DOC
company_bank_statement: [FILE]                    # PDF/Image
company_proof_of_address: [FILE]                  # PDF/Image
beneficiary_government_id: [FILE]                 # PDF/Image
beneficiary_source_of_funds: [FILE]               # PDF/Image
beneficiary_tax_id: [FILE]                        # PDF/Image
beneficiary_identity_document: [FILE]             # PDF/Image
additional_policies: [FILE]                       # PDF (Optional)
```

## Example cURL Request

### **Complete Example with All Data:**
```bash
curl --location 'http://192.168.0.146:8000/api/single-syndicate/create_syndicate/' \
--header 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
--form 'name=Tech Ventures Syndicate' \
--form 'description=A syndicate focused on early-stage technology investments' \
--form 'accredited=Yes' \
--form 'firm_name=Tech Ventures LLC' \
--form 'lp_network=Angel investors, VCs, Family offices' \
--form 'enable_lp_network=Yes' \
--form 'sector_ids=1,2,3' \
--form 'geography_ids=1,2,4' \
--form 'team_members=[
    {
        "name": "John Manager",
        "email": "john@techventures.com",
        "role": "Managing Partner",
        "description": "Experienced investor"
    }
]' \
--form 'beneficiaries=[
    {
        "name": "John Manager",
        "email": "john@techventures.com",
        "relationship": "Owner",
        "ownership_percentage": 100.00
    }
]' \
--form 'Risk_Regulatory_Attestation=This syndicate complies with all SEC regulations...' \
--form 'risk_regulatory_attestation=true' \
--form 'jurisdictional_requirements_check=true' \
--form 'additional_compliance_policies_check=true' \
--form 'self_knowledge_aml_policies=true' \
--form 'is_regulated_entity=true' \
--form 'is_ml_tf_risk=false' \
--form 'syndicate_logo=@/path/to/logo.png' \
--form 'company_certificate=@/path/to/certificate.pdf' \
--form 'company_bank_statement=@/path/to/bank_statement.pdf' \
--form 'company_proof_of_address=@/path/to/proof_of_address.pdf' \
--form 'beneficiary_government_id=@/path/to/government_id.pdf'
```

### **Minimal Example (Required Fields Only):**
```bash
curl --location 'http://192.168.0.146:8000/api/single-syndicate/create_syndicate/' \
--header 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
--form 'name=My Syndicate' \
--form 'description=Basic syndicate description' \
--form 'accredited=Yes' \
--form 'firm_name=My Firm LLC'
```

## Response Format

### **Success Response (201 Created):**
```json
{
    "success": true,
    "message": "Syndicate created successfully!",
    "syndicate_id": 1,
    "submission_id": "SYN-1-A1B2C3D4",
    "syndicate": {
        "id": 1,
        "name": "Tech Ventures Syndicate",
        "description": "A syndicate focused on early-stage technology investments",
        "accredited": "Yes",
        "firm_name": "Tech Ventures LLC",
        "manager": "username",
        "sectors": ["Technology", "Healthcare", "Finance"],
        "geographies": ["United States", "Canada", "United Kingdom"],
        "lp_network": "Angel investors, VCs, Family offices",
        "enable_lp_network": "Yes",
        "created_at": "2025-01-16T12:00:00Z"
    },
    "team_members": [
        {
            "name": "John Manager",
            "email": "john@techventures.com",
            "role": "Managing Partner",
            "description": "Experienced investor"
        }
    ],
    "beneficiaries": [
        {
            "name": "John Manager",
            "email": "john@techventures.com",
            "relationship": "Owner",
            "ownership_percentage": 100.00
        }
    ],
    "documents": [
        {
            "document_type": "syndicate_logo",
            "filename": "logo.png",
            "size": 1024000,
            "mime_type": "image/png",
            "uploaded_at": "2025-01-16T12:00:00Z"
        },
        {
            "document_type": "company_certificate",
            "filename": "certificate.pdf",
            "size": 2048000,
            "mime_type": "application/pdf",
            "uploaded_at": "2025-01-16T12:00:00Z"
        }
    ],
    "compliance": {
        "risk_regulatory_attestation": true,
        "jurisdictional_requirements": true,
        "additional_compliance_policies": true,
        "self_knowledge_aml_policies": true,
        "is_regulated_entity": true,
        "is_ml_tf_risk": false,
        "attested_at": "2025-01-16T12:00:00Z"
    }
}
```

### **Error Response (400 Bad Request):**
```json
{
    "error": "Syndicate name is required"
}
```

## Get Syndicate Details
**GET** `/api/single-syndicate/get_syndicate/?syndicate_id=1`

### Example:
```bash
curl --location 'http://192.168.0.146:8000/api/single-syndicate/get_syndicate/?syndicate_id=1' \
--header 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

## Frontend Integration Examples

### **JavaScript with FormData:**
```javascript
const formData = new FormData();

// Basic information
formData.append('name', 'Tech Ventures Syndicate');
formData.append('description', 'A syndicate focused on early-stage technology investments');
formData.append('accredited', 'Yes');
formData.append('firm_name', 'Tech Ventures LLC');

// Sectors and geographies
formData.append('sector_ids', '1,2,3');
formData.append('geography_ids', '1,2,4');

// Team members (JSON string)
formData.append('team_members', JSON.stringify([
    {
        name: 'John Manager',
        email: 'john@techventures.com',
        role: 'Managing Partner',
        description: 'Experienced investor'
    }
]));

// Beneficiaries (JSON string)
formData.append('beneficiaries', JSON.stringify([
    {
        name: 'John Manager',
        email: 'john@techventures.com',
        relationship: 'Owner',
        ownership_percentage: 100.00
    }
]));

// Compliance
formData.append('risk_regulatory_attestation', 'true');
formData.append('jurisdictional_requirements_check', 'true');
formData.append('additional_compliance_policies_check', 'true');
formData.append('self_knowledge_aml_policies', 'true');
formData.append('is_regulated_entity', 'true');
formData.append('is_ml_tf_risk', 'false');

// File uploads
formData.append('syndicate_logo', logoFile);
formData.append('company_certificate', certificateFile);
formData.append('company_bank_statement', bankStatementFile);

// Make the request
const response = await fetch('http://192.168.0.146:8000/api/single-syndicate/create_syndicate/', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${accessToken}`
    },
    body: formData
});

const result = await response.json();
console.log(result);
```

### **React Example:**
```jsx
import React, { useState } from 'react';

const SyndicateForm = () => {
    const [formData, setFormData] = useState({
        name: '',
        description: '',
        accredited: 'Yes',
        firm_name: '',
        // ... other fields
    });
    
    const [files, setFiles] = useState({});
    
    const handleSubmit = async (e) => {
        e.preventDefault();
        
        const submitData = new FormData();
        
        // Add all form fields
        Object.keys(formData).forEach(key => {
            submitData.append(key, formData[key]);
        });
        
        // Add team members and beneficiaries as JSON
        submitData.append('team_members', JSON.stringify(formData.team_members || []));
        submitData.append('beneficiaries', JSON.stringify(formData.beneficiaries || []));
        
        // Add files
        Object.keys(files).forEach(key => {
            if (files[key]) {
                submitData.append(key, files[key]);
            }
        });
        
        try {
            const response = await fetch('/api/single-syndicate/create_syndicate/', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
                },
                body: submitData
            });
            
            const result = await response.json();
            
            if (response.ok) {
                console.log('Syndicate created:', result);
                alert('Syndicate created successfully!');
            } else {
                console.error('Error:', result.error);
                alert('Error: ' + result.error);
            }
        } catch (error) {
            console.error('Network error:', error);
            alert('Network error occurred');
        }
    };
    
    return (
        <form onSubmit={handleSubmit}>
            {/* Your form fields here */}
            <input 
                type="text" 
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                placeholder="Syndicate Name"
                required
            />
            
            <input 
                type="file" 
                onChange={(e) => setFiles({...files, syndicate_logo: e.target.files[0]})}
                accept="image/*"
            />
            
            <button type="submit">Create Syndicate</button>
        </form>
    );
};
```

## Field Validation

### **Required Fields:**
- `name` - Syndicate name

### **Optional Fields:**
- All other fields are optional
- Documents can be uploaded later
- Team members and beneficiaries can be added later

### **Data Types:**
- **Text fields:** String
- **Boolean fields:** "true"/"false" strings
- **Arrays:** JSON strings or comma-separated values
- **Files:** File objects

## Error Handling

### **Common Errors:**
- **400 Bad Request:** Missing required fields or invalid data format
- **401 Unauthorized:** Invalid or missing authentication token
- **404 Not Found:** Syndicate not found (for GET requests)
- **413 Payload Too Large:** File size exceeds limit

### **Error Response Format:**
```json
{
    "error": "Detailed error message"
}
```

## Features

✅ **Single API Call** - Create complete syndicate in one request  
✅ **File Uploads** - Support for all document types  
✅ **Flexible Data** - JSON arrays or comma-separated values  
✅ **Complete Response** - Returns all created data  
✅ **Error Handling** - Comprehensive validation  
✅ **Authentication** - JWT token required  

## Notes

- All endpoints require authentication
- Files are automatically organized by syndicate and document type
- Original filenames are preserved for reference
- Team members and beneficiaries are stored as separate records
- Compliance attestations are tracked with timestamps
- The API handles both JSON arrays and comma-separated strings for flexibility
