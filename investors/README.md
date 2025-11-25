# Investors App - Complete 6-Step Onboarding

## Overview

The Investors app provides a comprehensive 6-step investor onboarding system with document upload, identity verification, bank details collection, and accreditation tracking - matching the Unlocksley platform UI screens.

## Features

✅ **6-Step Onboarding Process**
1. Basic Information
2. KYC / Identity Verification
3. Bank Details / Payment Setup
4. Accreditation (If Applicable - Optional)
5. Accept Agreements
6. Final Review & Submit

✅ **Document Upload Support**
- Government ID upload (Step 2)
- Bank proof upload (Step 3)
- Income/Net worth proof upload (Step 4)

✅ **Step Validation**
- Must complete steps in order
- Progress tracking
- Can't skip required steps

✅ **REST API with JWT Authentication**

✅ **Admin Interface**
- Review applications
- Manage investor profiles
- Track onboarding progress

## 6-Step Onboarding Flow

### Step 1: Basic Information
Collect investor's basic contact details:
- Full Name
- Email Address
- Phone Number
- Country of Residence

### Step 2: KYC / Identity Verification
Identity verification with document upload:
- Government-Issued ID (upload)
- Date of Birth
- Residential Address (street, city, state, zip, country)

### Step 3: Bank Details / Payment Setup
Payment information for fund transfers:
- Bank Account Number / Wallet Address
- Bank Name
- Account Holder's Name
- SWIFT/IFSC/Sort Code
- Proof of Bank Ownership (upload)

### Step 4: Accreditation (Optional)
Accreditation status (if applicable):
- Upload Proof of Income or Net Worth
- Are you an accredited investor? (Yes/No)
- Do you meet local investment thresholds? (Yes/No)

### Step 5: Accept Agreements
Legal agreements acceptance:
- ✓ Terms & Conditions
- ✓ Risk Disclosure
- ✓ Privacy Policy
- ✓ Confirmation of True Information

### Step 6: Final Review & Submit
Review all information and submit application for admin approval.

## Models

### InvestorProfile

Main model storing complete investor onboarding information.

**Key Fields:**
- User relationship (OneToOne with CustomUser)
- Step 1: full_name, email_address, phone_number, country_of_residence
- Step 2: government_id (file), date_of_birth, address fields
- Step 3: bank_account_number, bank_name, account_holder_name, swift_ifsc_code, proof_of_bank_ownership (file)
- Step 4: proof_of_income_net_worth (file), is_accredited_investor, meets_local_investment_thresholds
- Step 5: terms_and_conditions_accepted, risk_disclosure_accepted, privacy_policy_accepted, confirmation_of_true_information
- Application status tracking

**Properties:**
- `step1_completed` through `step6_completed`: Boolean indicators
- `current_step`: Integer (1-7) indicating workflow position

### Portfolio

Tracks investor's complete portfolio performance.

**Key Fields:**
- User relationship (OneToOne with CustomUser)
- total_invested, current_value, unrealized_gain
- portfolio_growth_percentage
- total_investments, active_investments, pending_investments
- Timestamps

**Methods:**
- `recalculate()`: Recalculates portfolio metrics from investments

### Investment

Individual investment tracking.

**Key Fields:**
- investor (FK to CustomUser)
- Syndicate details: name, ID, sector, geography
- investment_type: syndicate_deal, top_syndicate, invite
- Financial: amount_invested, current_value, target_amount, expected_return
- status: pending, active, completed, cancelled
- investment_date, investment_period

**Properties:**
- `gain_loss`: Calculated profit/loss
- `gain_loss_percentage`: Return percentage

### Notification

User notifications system.

**Key Fields:**
- user (FK to CustomUser)
- notification_type: investment, document, transfer, system
- title, message
- status: unread, read, archived
- priority: low, medium, high, urgent
- action_required, action_url
- metadata (JSON field)

**Methods:**
- `mark_as_read()`, `mark_as_unread()`

### KYCStatus

KYC verification status tracking.

**Key Fields:**
- investor (OneToOne with CustomUser)
- status: pending, under_review, approved, rejected, resubmit_required
- submitted_at, reviewed_at, approved_at
- reviewer_notes

## API Endpoints

**Base URL:** `/blockchain-backend/api/profiles/`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | POST | Create profile (Step 1) |
| `/my_profile/` | GET | Get user's profile |
| `/{id}/update_step1/` | PATCH | Update Step 1 |
| `/{id}/update_step2/` | PATCH | Update Step 2 (with file upload) |
| `/{id}/update_step3/` | PATCH | Update Step 3 (with file upload) |
| `/{id}/update_step4/` | PATCH | Update Step 4 (with file upload) |
| `/{id}/update_step5/` | PATCH | Update Step 5 |
| `/{id}/final_review/` | GET | Get final review data |
| `/{id}/submit_application/` | POST | Submit application |
| `/{id}/progress/` | GET | Get progress status |
| `/choices/` | GET | Get dropdown options |

**See [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) for complete API documentation with examples.**

## Serializers

### Step-Specific Serializers
- `InvestorProfileStep1Serializer`: Basic Information
- `InvestorProfileStep2Serializer`: KYC / Identity Verification
- `InvestorProfileStep3Serializer`: Bank Details / Payment Setup
- `InvestorProfileStep4Serializer`: Accreditation (Optional)
- `InvestorProfileStep5Serializer`: Accept Agreements
- `InvestorProfileStep6Serializer`: Final Review (Read-only)

### Other Serializers
- `InvestorProfileSerializer`: Complete profile data
- `InvestorProfileCreateSerializer`: Profile creation
- `InvestorProfileSubmitSerializer`: Application submission with validation

## ViewSets

### InvestorProfileViewSet

Complete ViewSet with:
- Standard CRUD operations
- Step-by-step update endpoints
- File upload support (MultiPartParser, FormParser)
- Progress tracking
- Final review display
- Application submission

**Custom Actions:**
- `my_profile()`: Get current user's profile
- `update_step1()` through `update_step5()`: Update individual steps
- `final_review()`: Display all info for review
- `submit_application()`: Submit for admin review
- `progress()`: Get completion status
- `choices()`: Get field options

## Admin Interface

**Features:**
- List view with filters (status, accreditation, country)
- Search by name, email, phone
- Organized fieldsets by step
- Progress tracking display
- Document links
- Read-only fields after submission
- Application status management

## Installation & Setup

Already configured in `INSTALLED_APPS`. Run migrations:

```bash
python manage.py makemigrations investors
python manage.py migrate investors
```

## Usage Example (React/JavaScript)

```javascript
// Step 1: Create Profile
const response = await fetch('/blockchain-backend/api/profiles/', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        full_name: 'John Doe',
        email_address: 'john@example.com',
        phone_number: '+1-555-0000',
        country_of_residence: 'United States'
    })
});
const profile = await response.json();

// Step 2: Upload KYC Documents
const formData = new FormData();
formData.append('government_id', fileInput.files[0]);
formData.append('date_of_birth', '1990-01-15');
formData.append('street_address', '123 Main Street');
formData.append('city', 'New York');
formData.append('state_province', 'New York');
formData.append('zip_postal_code', '10001');
formData.append('country', 'United States');

await fetch(`/blockchain-backend/api/profiles/${profile.id}/update_step2/`, {
    method: 'PATCH',
    headers: {'Authorization': `Bearer ${token}`},
    body: formData
});

// Continue with remaining steps...
// See API_DOCUMENTATION.md for complete examples
```

## File Uploads

### Configuration
- Upload path: `media/investor_documents/{user_id}/`
- Accepted formats: PDF, DOCX, JPG, JPEG, PNG
- Maximum size: 5MB per file

### Security
- Files stored securely in media folder
- Organized by user ID
- Protected access (authentication required)

## Validation Rules

### Step Progression
1. Steps must be completed in order (1 → 2 → 3 → 5 → 6)
2. Step 4 is optional
3. Cannot skip required steps
4. Each step validates previous steps are complete

### Field Validation
- **Step 1**: All fields required
- **Step 2**: All fields + government_id file required
- **Step 3**: All fields + proof_of_bank_ownership file required
- **Step 4**: Optional (if accredited, proof recommended)
- **Step 5**: All four agreements must be accepted

### Submission Validation
- Steps 1, 2, 3, and 5 must be completed
- Cannot submit twice
- Application status changes to "submitted"

## Application Status Workflow

```
draft → submitted → under_review → approved / rejected
```

1. **draft**: User filling out application (default)
2. **submitted**: Application submitted by user
3. **under_review**: Admin reviewing application
4. **approved**: Application approved - user can invest
5. **rejected**: Application rejected - user notified

## Database Schema

```sql
CREATE TABLE investors_investorprofile (
    id INTEGER PRIMARY KEY,
    user_id INTEGER UNIQUE,
    
    -- Step 1: Basic Information
    full_name VARCHAR(255),
    email_address VARCHAR(254),
    phone_number VARCHAR(20),
    country_of_residence VARCHAR(100),
    
    -- Step 2: KYC
    government_id VARCHAR(100),  -- File path
    date_of_birth DATE,
    street_address VARCHAR(255),
    city VARCHAR(100),
    state_province VARCHAR(100),
    zip_postal_code VARCHAR(20),
    country VARCHAR(100),
    
    -- Step 3: Bank Details
    bank_account_number VARCHAR(100),
    bank_name VARCHAR(255),
    account_holder_name VARCHAR(255),
    swift_ifsc_code VARCHAR(50),
    proof_of_bank_ownership VARCHAR(100),  -- File path
    
    -- Step 4: Accreditation (Optional)
    proof_of_income_net_worth VARCHAR(100),  -- File path
    is_accredited_investor BOOLEAN,
    meets_local_investment_thresholds BOOLEAN,
    
    -- Step 5: Agreements
    terms_and_conditions_accepted BOOLEAN,
    risk_disclosure_accepted BOOLEAN,
    privacy_policy_accepted BOOLEAN,
    confirmation_of_true_information BOOLEAN,
    
    -- Application Status
    application_status VARCHAR(20),
    application_submitted BOOLEAN,
    submitted_at DATETIME,
    
    -- Timestamps
    created_at DATETIME,
    updated_at DATETIME
);
```

## Testing

Run tests:
```bash
python manage.py test investors
```

## Monitoring & Analytics

Admins can track:
- Total applications submitted
- Applications by status
- Completion rates by step
- Average time to complete
- Accredited vs non-accredited investors

## Dashboard & Portfolio Features

✅ **Dashboard Overview**
- KYC status display
- Portfolio summary (total invested, current value, gains)
- Recent investments list
- Notification counts

✅ **Portfolio Management**
- Complete portfolio view with all investments
- Performance metrics and growth percentages
- Automatic recalculation of values
- Investment filtering by type, sector, status

✅ **Investment Tracking**
- Individual investment details
- Gain/loss calculations
- Filter by: Syndicate Deals, Top Syndicates, Invites
- Status tracking: Pending, Active, Completed, Cancelled

✅ **Notification System**
- Multi-type notifications: Investment, Document, Transfer, System
- Priority levels: Low, Medium, High, Urgent
- Action-required flagging
- Mark as read/unread
- Filtering and statistics

## Future Enhancements

- [ ] Email notifications at each step
- [ ] SMS verification for phone numbers
- [ ] Automated document verification (OCR)
- [ ] Integration with third-party KYC providers
- [ ] Multi-language support
- [ ] Mobile app compatibility
- [ ] Real-time portfolio updates via WebSockets
- [ ] Automated accreditation verification
- [ ] Webhook notifications for status changes
- [ ] Push notifications for mobile

## Related Apps

- **users**: CustomUser authentication
- **kyc**: Additional KYC verification
- **spv**: SPV management for investments
- **transfers**: Token transfer management
- **documents**: Document management system

## Support & Documentation

- **API Documentation**: [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
- **Main API**: `/blockchain-backend/api/`
- **Admin Interface**: `/blockchain-backend/admin/`

For issues or questions, contact the development team.
