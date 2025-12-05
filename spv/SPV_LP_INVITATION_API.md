# SPV LP Invitation APIs Documentation

Complete API endpoints for managing LP (Limited Partner) invitations for SPV deals.

---

## Base URL
```
/api/
```

---

## 1. Get/Send LP Invitations

**Endpoint:** `GET|POST /api/spv/{spv_id}/invite-lps/`

**Authentication:** Required (Bearer Token)

### GET - Get Current Invite Settings

**Description:** Retrieve current LP invitation settings for an SPV

**Response:**
```json
{
  "success": true,
  "data": {
    "spv_id": 1,
    "spv_name": "Tech Startup Fund Q4 2024",
    "current_invites": {
      "total_emails": 24,
      "emails": [
        "investor1@example.com",
        "investor2@example.com",
        "investor3@example.com"
      ],
      "message": "You are invited to invest in this opportunity...",
      "lead_carry_percentage": 5.0,
      "investment_visibility": "hidden",
      "auto_invite_active_spvs": false,
      "private_note": "Premium investor group",
      "tags": ["accredited", "tech-focused", "high-net-worth"]
    }
  }
}
```

---

### POST - Send LP Invitations

**Description:** Send invitations to LPs for an SPV

**Request Body:**
```json
{
  "emails": ["investor@example.com", "another@example.com"],
  "message": "You are invited to invest in Tech Startup Fund Q4 2024. This is a Series A opportunity in a fast-growing technology company.",
  "lead_carry_percentage": 5.0,
  "investment_visibility": "hidden",
  "auto_invite_active_spvs": false,
  "private_note": "Internal note about these investors",
  "tags": ["accredited", "tech-investors"]
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "LP invitations sent successfully to 2 new investor(s)",
  "data": {
    "spv_id": 1,
    "total_invited": 26,
    "new_invites_sent": 2,
    "emails_invited": ["investor@example.com", "another@example.com"],
    "all_emails": [
      "investor1@example.com",
      "investor2@example.com",
      "investor@example.com",
      "another@example.com"
    ],
    "settings": {
      "lead_carry_percentage": 5.0,
      "investment_visibility": "hidden",
      "auto_invite_active_spvs": false,
      "private_note": "Internal note about these investors",
      "tags": ["accredited", "tech-investors"]
    }
  }
}
```

**Status Code:** 201 Created

---

### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `emails` | array | ✓ | List of email addresses to invite |
| `message` | string | | Email message content |
| `lead_carry_percentage` | float | | Lead carry percentage (0-100) |
| `investment_visibility` | string | | "hidden" or "visible" |
| `auto_invite_active_spvs` | boolean | | Auto-invite to all active SPVs |
| `private_note` | string | | Internal notes (not sent to LPs) |
| `tags` | array | | Tags to categorize investors |

**Default Values:**
- `lead_carry_percentage`: 0.0
- `investment_visibility`: "hidden"
- `auto_invite_active_spvs`: false

**Validation:**
- Emails must be in valid format (abc@example.com)
- Duplicates automatically removed
- New emails merged with existing ones

---

## 2. Manage LP Default Settings

**Endpoint:** `GET|POST /api/spv/invite-lps/defaults/`

**Authentication:** Required

### GET - Get Default Settings

**Description:** Get user's default LP invitation settings

**Response:**
```json
{
  "success": true,
  "data": {
    "user_id": 5,
    "defaults": {
      "lead_carry_percentage": 5.0,
      "investment_visibility": "hidden",
      "auto_invite_active_spvs": false,
      "default_message": "You are invited to invest in this SPV opportunity. Please review the details and let us know if you are interested."
    }
  }
}
```

---

### POST - Set Default Settings

**Description:** Save user's default LP invitation settings

**Request Body:**
```json
{
  "lead_carry_percentage": 5.0,
  "investment_visibility": "hidden",
  "auto_invite_active_spvs": false,
  "default_message": "Custom default message for invitations"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Default LP invitation settings updated successfully",
  "data": {
    "user_id": 5,
    "defaults": {
      "lead_carry_percentage": 5.0,
      "investment_visibility": "hidden",
      "auto_invite_active_spvs": false,
      "default_message": "Custom default message for invitations"
    }
  }
}
```

---

## 3. Remove LP Invitation

**Endpoint:** `DELETE /api/spv/{spv_id}/invite-lps/{email}/`

**Authentication:** Required

**Description:** Remove a specific email from an SPV's invite list

**Parameters:**
- `spv_id` (integer, required): SPV ID
- `email` (string, required): Email address to remove (URL encoded)

**Response (Success):**
```json
{
  "success": true,
  "message": "Email investor@example.com removed from invite list",
  "data": {
    "spv_id": 1,
    "removed_email": "investor@example.com",
    "remaining_emails": [
      "investor1@example.com",
      "investor2@example.com"
    ],
    "total_remaining": 2
  }
}
```

**Status Code:** 200 OK

**Error Response (Email not found):**
```json
{
  "success": false,
  "error": "Email investor@example.com not found in invite list"
}
```

**Status Code:** 404 Not Found

**Example:**
```bash
curl -X DELETE "https://api.example.com/api/spv/1/invite-lps/investor%40example.com/" \
  -H "Authorization: Bearer TOKEN"
```

---

## 4. Bulk Invite LPs to Multiple SPVs

**Endpoint:** `PATCH /api/spv/bulk-invite-lps/`

**Authentication:** Required

**Description:** Send LP invitations to multiple SPVs at once

**Request Body:**
```json
{
  "spv_ids": [1, 2, 3],
  "emails": ["investor@example.com", "another@example.com"],
  "message": "You are invited to invest in multiple SPVs",
  "lead_carry_percentage": 5.0
}
```

**Response:**
```json
{
  "success": true,
  "message": "LP invitations sent to 3 SPV(s)",
  "data": {
    "spvs_updated": 3,
    "emails_invited": [
      "investor@example.com",
      "another@example.com"
    ],
    "spv_ids": [1, 2, 3],
    "settings": {
      "lead_carry_percentage": 5.0,
      "message": "You are invited to invest in multiple SPVs"
    }
  }
}
```

**Status Code:** 200 OK

---

## Error Responses

### 400 Bad Request
```json
{
  "success": false,
  "error": "emails field is required and must be a list of email addresses"
}
```

### Invalid Email Format
```json
{
  "success": false,
  "error": "Invalid email addresses: invalid.email, another@invalid"
}
```

### 403 Forbidden
```json
{
  "error": "You do not have permission to access this SPV"
}
```

### 404 Not Found
```json
{
  "success": false,
  "error": "Some SPVs not found. Found 2 out of 3"
}
```

---

## Usage Examples

### Send Invitations to Single SPV
```bash
curl -X POST "https://api.example.com/api/spv/1/invite-lps/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "emails": ["investor@example.com", "another@example.com"],
    "message": "Investment opportunity in Tech Startup",
    "lead_carry_percentage": 5.0,
    "tags": ["accredited", "tech-focused"]
  }'
```

### Get Current Invites
```bash
curl -X GET "https://api.example.com/api/spv/1/invite-lps/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Remove Specific LP
```bash
curl -X DELETE "https://api.example.com/api/spv/1/invite-lps/investor%40example.com/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Set Default Settings
```bash
curl -X POST "https://api.example.com/api/spv/invite-lps/defaults/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "lead_carry_percentage": 5.0,
    "investment_visibility": "hidden",
    "default_message": "You are invited..."
  }'
```

### Bulk Invite to Multiple SPVs
```bash
curl -X PATCH "https://api.example.com/api/spv/bulk-invite-lps/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "spv_ids": [1, 2, 3],
    "emails": ["investor@example.com"],
    "message": "Multi-SPV investment opportunity",
    "lead_carry_percentage": 5.0
  }'
```

---

## Field Reference

### investment_visibility Options
- `hidden` - Investment amounts not visible to other LPs
- `visible` - Investment amounts visible to all LPs

### Tags
Custom tags for categorizing investors:
- `accredited` - Accredited investor
- `high-net-worth` - High net worth individual
- `institutional` - Institutional investor
- `tech-focused` - Technology sector interest
- `healthcare-focused` - Healthcare sector interest
- `early-stage` - Early stage preference
- `established-ve` - Established venture experience

---

## Response Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK - Success |
| 201 | Created - Invitations sent |
| 400 | Bad Request - Invalid data |
| 403 | Forbidden - No permission |
| 404 | Not Found - SPV or email not found |

---

## Authorization & Permissions

- **Required**: JWT Bearer Token
- **Access Control**: Users can only manage invitations for SPVs they created
- **Admin**: Admins can manage invitations for any SPV
- **Response**: 403 Forbidden if unauthorized

---

## Features

✅ Single and bulk LP invitations
✅ Email validation
✅ Duplicate detection and removal
✅ Customizable invitation messages
✅ Carry percentage configuration
✅ Investment visibility controls
✅ Auto-invite settings
✅ Private notes and tagging
✅ Default settings management
✅ Comprehensive error handling

---

## Notes

- Email addresses are validated against standard email regex
- Duplicate emails are automatically filtered out
- New emails are merged with existing invites (merge, not replace)
- Lead carry percentage is user/SPV specific
- Investment visibility applies to valuations and fund performance
- Auto-invite setting can automatically add LPs to new active SPVs
- Tags help organize and manage investor groups
- Emails sent through integration (configure email service)

