# Syndicate Creation Flow with Document Uploads

This guide covers the complete multi-step syndicate creation flow with document upload support, matching your frontend design.

## Base URL
```
http://127.0.0.1:8000/api/syndicate-flow/
```

## Complete Syndicate Creation Flow

### Step 1: Lead Info
**POST** `/api/syndicate-flow/step1_lead_info/`

Create syndicate with basic information.

**Request Body:**
```json
{
    "name": "Tech Ventures Syndicate",
    "description": "A syndicate focused on early-stage technology investments",
    "accredited": "Yes",
    "sector_ids": [1, 2, 3],
    "geography_ids": [1, 2, 4],
    "lp_network": "Angel investors, VCs, Family offices",
    "enable_lp_network": "Yes"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Step 1 completed successfully",
    "syndicate_id": 1,
    "syndicate": {
        "id": 1,
        "name": "Tech Ventures Syndicate",
        "description": "A syndicate focused on early-stage technology investments",
        "accredited": "Yes",
        "manager": 18,
        "sectors": [...],
        "geographies": [...]
    },
    "next_step": "step2_entity_profile"
}
```

### Step 2: Entity Profile (with Logo Upload)
**POST** `/api/syndicate-flow/step2_entity_profile/`

**Content-Type:** `multipart/form-data`

**Form Data:**
```
syndicate_id: 1
firm_name: Tech Ventures LLC
syndicate_logo: [FILE] (logo image)
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

**Response:**
```json
{
    "success": true,
    "message": "Step 2 completed successfully",
    "syndicate_id": 1,
    "next_step": "step3_kyb_verification"
}
```

### Step 3: KYB Verification (with Document Uploads)
**POST** `/api/syndicate-flow/step3_kyb_verification/`

**Content-Type:** `multipart/form-data`

**Form Data:**
```
syndicate_id: 1
company_certificate: [FILE] (PDF/DOC)
company_bank_statement: [FILE] (PDF/IMAGE)
company_proof_of_address: [FILE] (PDF/IMAGE)
beneficiary_government_id: [FILE] (PDF/IMAGE)
beneficiary_source_of_funds: [FILE] (PDF/IMAGE)
beneficiary_tax_id: [FILE] (PDF/IMAGE)
beneficiary_identity_document: [FILE] (PDF/IMAGE)
beneficiaries: [
    {
        "name": "John Manager",
        "email": "john@techventures.com",
        "relationship": "Owner",
        "ownership_percentage": 100.00
    }
]
```

**Response:**
```json
{
    "success": true,
    "message": "Step 3 completed successfully",
    "syndicate_id": 1,
    "next_step": "step4_compliance"
}
```

### Step 4: Compliance & Attestation
**POST** `/api/syndicate-flow/step4_compliance/`

**Content-Type:** `multipart/form-data`

**Form Data:**
```
syndicate_id: 1
Risk_Regulatory_Attestation: "This syndicate complies with all SEC regulations..."
jurisdictional_requirements: "United States, Canada, United Kingdom"
additional_compliance_policies: "KYC/AML policies enforced..."
risk_regulatory_attestation: true
jurisdictional_requirements_check: true
additional_compliance_policies_check: true
self_knowledge_aml_policies: true
is_regulated_entity: true
is_ml_tf_risk: false
attestation_text: "I attest that all information is accurate..."
additional_policies: [FILE] (optional PDF)
```

**Response:**
```json
{
    "success": true,
    "message": "Step 4 completed successfully",
    "syndicate_id": 1,
    "next_step": "step5_final_review"
}
```

### Step 5: Final Review
**POST** `/api/syndicate-flow/step5_final_review/`

**Request Body:**
```json
{
    "syndicate_id": 1
}
```

**Response:**
```json
{
    "success": true,
    "message": "Final review data prepared successfully",
    "review_data": {
        "syndicate": {...},
        "team_members": [...],
        "beneficiaries": [...],
        "documents": [
            {
                "document_type": "syndicate_logo",
                "original_filename": "logo.png",
                "file_size": 1024000,
                "mime_type": "image/png",
                "uploaded_at": "2025-01-16T12:00:00Z",
                "is_verified": false
            },
            {
                "document_type": "company_certificate",
                "original_filename": "certificate.pdf",
                "file_size": 2048000,
                "mime_type": "application/pdf",
                "uploaded_at": "2025-01-16T12:05:00Z",
                "is_verified": false
            }
        ],
        "compliance": {...}
    },
    "next_step": "submit"
}
```

### Step 6: Submit Syndicate
**POST** `/api/syndicate-flow/submit_syndicate/`

**Request Body:**
```json
{
    "syndicate_id": 1
}
```

**Response:**
```json
{
    "success": true,
    "message": "Syndicate application submitted successfully!",
    "syndicate": {...},
    "submission_id": "SYN-1-A1B2C3D4"
}
```

## Document Upload Examples

### Using cURL for File Uploads

#### Step 2: Upload Logo
```bash
curl --location 'http://127.0.0.1:8000/api/syndicate-flow/step2_entity_profile/' \
--header 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
--form 'syndicate_id=1' \
--form 'firm_name=Tech Ventures LLC' \
--form 'syndicate_logo=@/path/to/logo.png' \
--form 'team_members=[
    {
        "name": "John Manager",
        "email": "john@techventures.com",
        "role": "Managing Partner",
        "description": "Experienced investor"
    }
]'
```

#### Step 3: Upload KYB Documents
```bash
curl --location 'http://127.0.0.1:8000/api/syndicate-flow/step3_kyb_verification/' \
--header 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
--form 'syndicate_id=1' \
--form 'company_certificate=@/path/to/certificate.pdf' \
--form 'company_bank_statement=@/path/to/bank_statement.pdf' \
--form 'company_proof_of_address=@/path/to/proof_of_address.pdf' \
--form 'beneficiary_government_id=@/path/to/government_id.pdf' \
--form 'beneficiaries=[
    {
        "name": "John Manager",
        "email": "john@techventures.com",
        "relationship": "Owner",
        "ownership_percentage": 100.00
    }
]'
```

#### Step 4: Upload Additional Policies
```bash
curl --location 'http://127.0.0.1:8000/api/syndicate-flow/step4_compliance/' \
--header 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
--form 'syndicate_id=1' \
--form 'Risk_Regulatory_Attestation=This syndicate complies with all SEC regulations...' \
--form 'risk_regulatory_attestation=true' \
--form 'jurisdictional_requirements_check=true' \
--form 'additional_compliance_policies_check=true' \
--form 'self_knowledge_aml_policies=true' \
--form 'is_regulated_entity=true' \
--form 'is_ml_tf_risk=false' \
--form 'additional_policies=@/path/to/additional_policies.pdf'
```

## Document Types Supported

### Company Documents:
- **company_certificate** - Company Certificate of Incorporation
- **company_bank_statement** - Company Bank Statement (Most Recent 3 Months)
- **company_proof_of_address** - Company Proof of Address

### Beneficiary Documents:
- **beneficiary_government_id** - Beneficiary Government ID Proof
- **beneficiary_source_of_funds** - Beneficiary Source of Funds Proof
- **beneficiary_tax_id** - Beneficiary Tax ID Proof
- **beneficiary_identity_document** - Beneficiary Identity Document

### Other Documents:
- **syndicate_logo** - Syndicate Logo (Image)
- **additional_policies** - Additional Compliance Policies (Optional)

## File Upload Specifications

### Supported File Types:
- **Images:** PNG, JPG, JPEG, GIF
- **Documents:** PDF, DOC, DOCX
- **Maximum File Size:** 10MB per file

### File Storage:
- Files are stored in: `media/syndicate_documents/{syndicate_id}/{document_type}/`
- Original filenames are preserved
- File metadata is tracked (size, MIME type, upload date)

## Progress Tracking

### Get Syndicate Progress:
```bash
curl --location 'http://127.0.0.1:8000/api/syndicate-flow/get_syndicate_progress/?syndicate_id=1' \
--header 'Authorization: Bearer YOUR_ACCESS_TOKEN'
```

**Response:**
```json
{
    "syndicate_id": 1,
    "progress": {
        "step1_completed": true,
        "step2_completed": true,
        "step3_completed": true,
        "step4_completed": false,
        "current_step": "step4_compliance"
    },
    "syndicate_data": {...}
}
```

## Frontend Integration

### JavaScript Example with File Uploads:

```javascript
// Step 2: Entity Profile with Logo Upload
const formData = new FormData();
formData.append('syndicate_id', '1');
formData.append('firm_name', 'Tech Ventures LLC');
formData.append('syndicate_logo', logoFile); // File from input
formData.append('team_members', JSON.stringify([
    {
        name: 'John Manager',
        email: 'john@techventures.com',
        role: 'Managing Partner',
        description: 'Experienced investor'
    }
]));

const response = await fetch('/api/syndicate-flow/step2_entity_profile/', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${accessToken}`
    },
    body: formData
});

// Step 3: KYB Verification with Multiple Documents
const kybFormData = new FormData();
kybFormData.append('syndicate_id', '1');
kybFormData.append('company_certificate', certificateFile);
kybFormData.append('company_bank_statement', bankStatementFile);
kybFormData.append('company_proof_of_address', proofOfAddressFile);
kybFormData.append('beneficiary_government_id', governmentIdFile);
kybFormData.append('beneficiaries', JSON.stringify(beneficiaries));

const kybResponse = await fetch('/api/syndicate-flow/step3_kyb_verification/', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${accessToken}`
    },
    body: kybFormData
});
```

## Error Handling

### Common Errors:
- **400 Bad Request:** Missing required fields or invalid data
- **404 Not Found:** Syndicate not found or access denied
- **413 Payload Too Large:** File size exceeds limit
- **415 Unsupported Media Type:** Invalid file type

### Error Response Format:
```json
{
    "error": "File size exceeds maximum limit of 10MB"
}
```

## Features

✅ **Multi-Step Flow** - Matches your frontend design exactly  
✅ **Document Uploads** - Support for all document types  
✅ **File Validation** - Size and type checking  
✅ **Progress Tracking** - Know which step you're on  
✅ **Team Management** - Add multiple team members  
✅ **Beneficiary Management** - Track ownership percentages  
✅ **Compliance Tracking** - Full audit trail  
✅ **File Metadata** - Track upload details  

## Notes

- All endpoints require authentication
- Files are automatically organized by syndicate and document type
- Original filenames are preserved for reference
- Upload progress can be tracked through the progress endpoint
- Documents can be verified by admins through the admin interface
