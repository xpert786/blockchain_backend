# 🚀 Syndicate Onboarding API Testing Guide

## 📋 Overview
This guide covers the complete syndicate onboarding flow with 4 main steps:
1. **Step 1: Lead Info** - Personal and accreditation details
2. **Step 2: Entity Profile** - Company information and structure  
3. **Step 3: Compliance & Attestation** - Regulatory requirements
4. **Step 4: Final Review & Submit** - Review and submit application

## 🔧 Prerequisites
1. **Django Server Running**: Make sure your Django server is running on `http://localhost:8000`
2. **Postman Installed**: Download and install Postman from https://www.postman.com/downloads/
3. **Database Migrated**: Ensure all migrations are applied (`python manage.py migrate`)
4. **Sample Data**: Create some sectors and geographies for testing

## 🛠️ Setup Instructions

### 1. Import Postman Collection
1. Open Postman
2. Click "Import" button
3. Select the `Syndicate_Onboarding_Postman_Collection.json` file
4. The collection will be imported with all endpoints organized in folders

### 2. Set Environment Variables
1. In Postman, click on the "Environments" tab
2. Create a new environment called "Syndicate Onboarding"
3. Add these variables:
   - `base_url`: `http://localhost:8000/blockchain-backend`
   - `access_token`: (leave empty, will be filled automatically)
   - `admin_access_token`: (leave empty, for admin operations)

### 3. Create Sample Data
First, create some sectors and geographies for testing:

```bash
# Run Django shell
python manage.py shell

# Create sample sectors
from users.models import Sector, Geography

# Create sectors
sectors = [
    ("Fintech", "Financial technology companies"),
    ("Healthcare", "Healthcare and medical technology"),
    ("Technology", "General technology companies"),
    ("AI/ML", "Artificial Intelligence and Machine Learning"),
    ("SaaS", "Software as a Service companies")
]

for name, desc in sectors:
    Sector.objects.get_or_create(name=name, defaults={'description': desc})

# Create geographies
geographies = [
    ("North America", "North America", "NA"),
    ("Europe", "Europe", "EU"),
    ("Asia Pacific", "Asia Pacific", "AP"),
    ("United States", "North America", "US"),
    ("United Kingdom", "Europe", "GB")
]

for name, region, code in geographies:
    Geography.objects.get_or_create(name=name, defaults={'region': region, 'country_code': code})
```

## 🧪 Complete Testing Workflow

### Phase 1: User Registration (Prerequisites)
1. **Register Syndicate User**
   - Run "1. User Registration (Syndicate Role)"
   - **Request Body**: Update with your test data
   - **Expected**: 201 Created with access_token
   - **Action**: Copy the `access` token from response and paste it into the `access_token` environment variable

2. **Complete Registration Flow**
   - Run "2. Complete Registration Flow" (choose email verification)
   - Run "3. Verify OTP Code" (use actual OTP from email)
   - Run "4. Accept Terms of Service"
   - Run "5. Complete Registration"

### Phase 2: Syndicate Onboarding
1. **Get Available Data**
   - Run "Get Available Sectors & Geographies"
   - **Expected**: List of sectors and geographies with IDs
   - **Action**: Note the IDs for use in subsequent requests

2. **Step 1: Lead Info**
   - Run "Step 1: Lead Info - Personal & Accreditation"
   - **Request Body**: Update `sector_ids` and `geography_ids` with actual IDs from previous step
   - **Expected**: 200 OK with step completion status
   - **Fields**:
     - `is_accredited`: "yes" or "no"
     - `understands_regulatory_requirements`: true
     - `sector_ids`: Array of sector IDs
     - `geography_ids`: Array of geography IDs
     - `existing_lp_count`: "0", "1-10", "11-25", "26-50", "51-100", "100+"
     - `enable_platform_lp_access`: true/false

3. **Step 2: Entity Profile**
   - Run "Step 2: Entity Profile - Company Information"
   - **Expected**: 200 OK with step completion status
   - **Fields**:
     - `firm_name`: Company/syndicate name
     - `description`: Detailed description
     - `logo`: File upload (optional)

4. **Step 3: Compliance & Attestation**
   - Run "Step 3: Compliance & Attestation"
   - **Expected**: 200 OK with step completion status
   - **Fields**:
     - `risk_regulatory_attestation`: true
     - `jurisdictional_compliance_acknowledged`: true
     - `additional_compliance_policies`: File upload (optional)

5. **Step 4: Final Review & Submit**
   - Run "Step 4: Final Review & Submit"
   - **Expected**: 200 OK with submission confirmation
   - **Fields**:
     - `application_submitted`: true

### Phase 3: Profile Management
1. **Check Progress**
   - Run "Get Syndicate Progress"
   - **Expected**: Complete progress status with all steps marked as completed

2. **View Profile**
   - Run "Get Syndicate Profile"
   - **Expected**: Complete profile with all data and step completion status

## 📊 Expected Responses

### Successful Step 1 Response
```json
{
    "success": true,
    "message": "Step 1 completed successfully",
    "profile": {
        "id": 1,
        "user": 1,
        "is_accredited": "yes",
        "understands_regulatory_requirements": true,
        "sectors": [
            {"id": 1, "name": "Fintech", "description": "Financial technology companies"},
            {"id": 2, "name": "Healthcare", "description": "Healthcare and medical technology"}
        ],
        "geographies": [
            {"id": 1, "name": "North America", "region": "North America"},
            {"id": 2, "name": "Europe", "region": "Europe"}
        ],
        "existing_lp_count": "11-25",
        "enable_platform_lp_access": true,
        "step1_completed": true,
        "step2_completed": false,
        "step3_completed": false,
        "step4_completed": false,
        "current_step": 2,
        "application_status": "draft"
    },
    "next_step": "step2"
}
```

### Successful Final Submission Response
```json
{
    "success": true,
    "message": "Syndicate application submitted successfully! Your application is now under review.",
    "profile": {
        "id": 1,
        "application_submitted": true,
        "submitted_at": "2024-01-15T10:30:00Z",
        "application_status": "submitted",
        "step1_completed": true,
        "step2_completed": true,
        "step3_completed": true,
        "step4_completed": true,
        "current_step": 5
    },
    "application_status": "submitted",
    "submitted_at": "2024-01-15T10:30:00Z"
}
```

## 🚨 Common Issues & Solutions

### Issue 1: "Only users with syndicate role can access this endpoint"
- **Solution**: Make sure the user was registered with `"role": "syndicate"`

### Issue 2: "Step X must be completed before proceeding to Step Y"
- **Solution**: Complete the previous steps in order. Check step completion status.

### Issue 3: "At least one sector must be selected"
- **Solution**: Provide valid sector IDs in the `sector_ids` array

### Issue 4: "At least one geography must be selected"
- **Solution**: Provide valid geography IDs in the `geography_ids` array

### Issue 5: "Accreditation status is required"
- **Solution**: Set `is_accredited` to "yes" or "no"

### Issue 6: "Firm name is required"
- **Solution**: Provide a valid `firm_name` in Step 2

### Issue 7: "Risk & Regulatory Attestation is required"
- **Solution**: Set `risk_regulatory_attestation` to true in Step 3

## 🔄 Step Validation Rules

### Step 1 Requirements:
- ✅ `is_accredited` must be "yes" or "no"
- ✅ `understands_regulatory_requirements` must be true
- ✅ At least one sector must be selected
- ✅ At least one geography must be selected
- ✅ `existing_lp_count` must be provided

### Step 2 Requirements:
- ✅ `firm_name` must be provided
- ✅ `description` must be provided
- ✅ Step 1 must be completed

### Step 3 Requirements:
- ✅ `risk_regulatory_attestation` must be true
- ✅ `jurisdictional_compliance_acknowledged` must be true
- ✅ Step 2 must be completed

### Step 4 Requirements:
- ✅ `application_submitted` must be true
- ✅ Steps 1, 2, and 3 must be completed

## 📝 Testing Checklist

- [ ] User registration with syndicate role
- [ ] Complete registration flow (verification, terms)
- [ ] Get available sectors and geographies
- [ ] Step 1: Lead Info completion
- [ ] Step 2: Entity Profile completion
- [ ] Step 3: Compliance & Attestation completion
- [ ] Step 4: Final Review & Submit
- [ ] Profile retrieval and progress checking
- [ ] Admin profile updates (if admin access available)

## 🎯 Key Features Tested

- **Role-based Access**: Only syndicate users can access onboarding
- **Step Validation**: Each step validates previous step completion
- **Data Relationships**: Sectors and geographies are properly linked
- **File Uploads**: Logo and compliance policy uploads
- **Progress Tracking**: Real-time step completion status
- **Application Status**: Draft → Submitted → Under Review → Approved/Rejected
- **Admin Management**: Admin can update profiles and status

## 🆘 Support

If you encounter any issues:
1. Check the Django server logs
2. Verify all environment variables are set
3. Ensure the database is properly migrated
4. Check that all required fields are included in requests
5. Verify that previous steps are completed before proceeding
6. Check that sectors and geographies exist in the database

## 📈 Next Steps

After completing the syndicate onboarding:
1. **Admin Review**: Administrators can review applications in Django admin
2. **Status Updates**: Update application status (approved/rejected)
3. **Additional Features**: Add team members, investment preferences, etc.
4. **Integration**: Connect with frontend application for UI testing
