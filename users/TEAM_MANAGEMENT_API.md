# Team Management API Documentation

## Overview

The Team Management API allows syndicate managers to add, manage, and configure team members with role-based permissions. This system supports both role-based access controls (RBAC) and individual permission overrides.

## Base URL

```
/blockchain-backend/api/
```

## Authentication

All endpoints require:
- **Authentication**: JWT Bearer token
- **Role**: User must have `role='syndicate'`
- **Permission**: User must be syndicate owner OR team member with `can_manage_team=True`

---

## API Endpoints

### 1. List Team Members

Get all team members for the current syndicate.

```http
GET /api/team-members/
```

**Query Parameters:**
- `search` - Search by name, email, or role
- `role` - Filter by role (manager, analyst, associate, partner, admin, viewer)
- `is_active` - Filter by active status (true/false)

**Response:**
```json
[
  {
    "id": 1,
    "name": "Mason Harper",
    "email": "mason@example.com",
    "role": "manager",
    "user_detail": {
      "id": 5,
      "username": "mason",
      "email": "mason@example.com",
      "first_name": "Mason",
      "last_name": "Harper"
    },
    "can_access_dashboard": true,
    "is_active": true,
    "is_registered": true,
    "added_at": "2025-11-20T10:00:00Z"
  },
  {
    "id": 2,
    "name": "Carter Jack",
    "email": "carter@example.com",
    "role": "analyst",
    "user_detail": null,
    "can_access_dashboard": true,
    "is_active": true,
    "is_registered": false,
    "added_at": "2025-11-21T14:30:00Z"
  }
]
```

---

### 2. Get Team Member Details

Get detailed information about a specific team member.

```http
GET /api/team-members/{id}/
```

**Response:**
```json
{
  "id": 1,
  "syndicate": 1,
  "user": 5,
  "user_detail": {
    "id": 5,
    "username": "mason",
    "email": "mason@example.com",
    "first_name": "Mason",
    "last_name": "Harper"
  },
  "name": "Mason Harper",
  "email": "mason@example.com",
  "role": "manager",
  "permissions": {
    "can_access_dashboard": true,
    "can_manage_spvs": true,
    "can_manage_documents": true,
    "can_manage_investors": true,
    "can_view_reports": true,
    "can_manage_transfers": true,
    "can_manage_team": true,
    "can_manage_settings": true
  },
  "can_access_dashboard": true,
  "can_manage_spvs": true,
  "can_manage_documents": true,
  "can_manage_investors": true,
  "can_view_reports": true,
  "can_manage_transfers": true,
  "can_manage_team": true,
  "can_manage_settings": true,
  "invitation_sent": false,
  "invitation_accepted": false,
  "is_active": true,
  "is_registered": true,
  "added_by": 1,
  "added_by_detail": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "added_at": "2025-11-20T10:00:00Z",
  "updated_at": "2025-11-25T15:30:00Z"
}
```

---

### 3. Add Team Member

Add a new team member to the syndicate.

```http
POST /api/team-members/
```

**Request Body:**
```json
{
  "name": "Carter Jack",
  "email": "carter@example.com",
  "role": "analyst",
  "can_access_dashboard": true,
  "can_manage_spvs": false,
  "can_manage_documents": true,
  "can_manage_investors": false,
  "can_view_reports": true,
  "can_manage_transfers": false,
  "can_manage_team": false,
  "can_manage_settings": false
}
```

**Note:** If RBAC is enabled (`enable_role_based_access_controls=true`), permissions will be auto-set based on role. Manual permissions will be ignored.

**Response:** (201 Created)
```json
{
  "message": "Team member added successfully",
  "data": {
    "id": 2,
    "name": "Carter Jack",
    "email": "carter@example.com",
    "role": "analyst",
    "permissions": {
      "can_access_dashboard": true,
      "can_manage_spvs": false,
      "can_manage_documents": true,
      "can_manage_investors": false,
      "can_view_reports": true,
      "can_manage_transfers": false,
      "can_manage_team": false,
      "can_manage_settings": false
    },
    "is_active": true,
    "is_registered": false,
    "added_at": "2025-11-27T10:00:00Z"
  }
}
```

---

### 4. Update Team Member

Update team member details, role, and permissions.

```http
PATCH /api/team-members/{id}/
```

**Request Body:**
```json
{
  "role": "partner",
  "can_manage_spvs": true,
  "can_manage_transfers": true,
  "is_active": true
}
```

**Response:**
```json
{
  "message": "Team member updated successfully",
  "data": {
    "id": 2,
    "name": "Carter Jack",
    "email": "carter@example.com",
    "role": "partner",
    "permissions": {
      "can_access_dashboard": true,
      "can_manage_spvs": true,
      "can_manage_documents": true,
      "can_manage_investors": true,
      "can_view_reports": true,
      "can_manage_transfers": true,
      "can_manage_team": false,
      "can_manage_settings": false
    },
    "is_active": true
  }
}
```

---

### 5. Update Role Only

Update only the team member's role.

```http
PATCH /api/team-members/{id}/update_role/
```

**Request Body:**
```json
{
  "role": "manager",
  "apply_role_permissions": true
}
```

**Parameters:**
- `role` - New role (manager, analyst, associate, partner, admin, viewer)
- `apply_role_permissions` - Whether to apply default role permissions (default: true)

**Response:**
```json
{
  "message": "Role updated successfully",
  "data": {
    "id": 2,
    "name": "Carter Jack",
    "role": "manager",
    "permissions": {
      "can_access_dashboard": true,
      "can_manage_spvs": true,
      "can_manage_documents": true,
      "can_manage_investors": true,
      "can_view_reports": true,
      "can_manage_transfers": true,
      "can_manage_team": true,
      "can_manage_settings": true
    }
  }
}
```

---

### 6. Update Permissions Only

Update only specific permissions without changing role.

```http
PATCH /api/team-members/{id}/update_permissions/
```

**Request Body:**
```json
{
  "can_manage_documents": true,
  "can_manage_transfers": false,
  "can_manage_team": true
}
```

**Response:**
```json
{
  "message": "Permissions updated successfully",
  "data": {
    "id": 2,
    "name": "Carter Jack",
    "role": "analyst",
    "permissions": {
      "can_access_dashboard": true,
      "can_manage_spvs": false,
      "can_manage_documents": true,
      "can_manage_investors": false,
      "can_view_reports": true,
      "can_manage_transfers": false,
      "can_manage_team": true,
      "can_manage_settings": false
    }
  }
}
```

---

### 7. Remove Team Member

Remove a team member from the syndicate.

```http
DELETE /api/team-members/{id}/
```

**Response:**
```json
{
  "message": "Team member removed successfully"
}
```

---

### 8. Deactivate Team Member

Temporarily deactivate a team member without removing them.

```http
POST /api/team-members/{id}/deactivate/
```

**Response:**
```json
{
  "message": "Team member deactivated successfully",
  "data": {
    "id": 2,
    "name": "Carter Jack",
    "is_active": false
  }
}
```

---

### 9. Activate Team Member

Reactivate a previously deactivated team member.

```http
POST /api/team-members/{id}/activate/
```

**Response:**
```json
{
  "message": "Team member activated successfully",
  "data": {
    "id": 2,
    "name": "Carter Jack",
    "is_active": true
  }
}
```

---

### 10. Get Available Roles

Get list of all available roles.

```http
GET /api/team-members/roles/
```

**Response:**
```json
{
  "success": true,
  "data": {
    "roles": [
      {"value": "manager", "label": "Manager"},
      {"value": "analyst", "label": "Analyst"},
      {"value": "associate", "label": "Associate"},
      {"value": "partner", "label": "Partner"},
      {"value": "admin", "label": "Admin"},
      {"value": "viewer", "label": "Viewer"}
    ]
  }
}
```

---

### 11. Get Permissions List

Get list of all available permissions.

```http
GET /api/team-members/permissions_list/
```

**Response:**
```json
{
  "success": true,
  "data": {
    "permissions": [
      {"key": "can_access_dashboard", "label": "Access Dashboard"},
      {"key": "can_manage_spvs", "label": "Manage SPVs"},
      {"key": "can_manage_documents", "label": "Manage Documents"},
      {"key": "can_manage_investors", "label": "Manage Investors"},
      {"key": "can_view_reports", "label": "View Reports"},
      {"key": "can_manage_transfers", "label": "Manage Transfers"},
      {"key": "can_manage_team", "label": "Manage Team"},
      {"key": "can_manage_settings", "label": "Manage Settings"}
    ]
  }
}
```

---

### 12. Get Team Statistics

Get statistics about team members.

```http
GET /api/team-members/statistics/
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total_members": 6,
    "active_members": 5,
    "inactive_members": 1,
    "registered_members": 3,
    "pending_invitations": 2,
    "role_distribution": {
      "manager": 1,
      "analyst": 2,
      "associate": 1,
      "partner": 1,
      "admin": 0,
      "viewer": 1
    }
  }
}
```

---

### 13. Team Management Settings

Get team management overview with RBAC settings.

```http
GET /api/syndicate/settings/team-management/
PATCH /api/syndicate/settings/team-management/
```

**GET Response:**
```json
{
  "success": true,
  "data": {
    "syndicate_id": 1,
    "firm_name": "Tech Ventures LLC",
    "enable_role_based_access_controls": true,
    "team_members_count": 6,
    "team_members": [
      {
        "id": 1,
        "name": "Mason Harper",
        "email": "mason@example.com",
        "role": "manager",
        "is_active": true
      }
    ]
  }
}
```

**PATCH Request (Update RBAC):**
```json
{
  "enable_role_based_access_controls": false
}
```

**PATCH Response:**
```json
{
  "success": true,
  "message": "Role-based access controls updated successfully",
  "data": {
    "enable_role_based_access_controls": false
  }
}
```

---

## Role-Based Permissions Matrix

| Role | Dashboard | SPVs | Documents | Investors | Reports | Transfers | Team | Settings |
|------|-----------|------|-----------|-----------|---------|-----------|------|----------|
| **Manager** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Partner** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Admin** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Associate** | ✅ | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Analyst** | ✅ | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ |
| **Viewer** | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |

---

## Complete Workflow Examples

### Workflow 1: Add Team Member with RBAC Enabled

```javascript
// 1. Add team member with role
const response = await fetch('/api/team-members/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: 'Carter Jack',
    email: 'carter@example.com',
    role: 'analyst'
    // Permissions auto-applied based on role if RBAC enabled
  })
});

const result = await response.json();
console.log(result.message); // "Team member added successfully"
```

### Workflow 2: Update Role and Apply Default Permissions

```javascript
// Update role and reset permissions to role defaults
const response = await fetch('/api/team-members/2/update_role/', {
  method: 'PATCH',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    role: 'manager',
    apply_role_permissions: true
  })
});

const result = await response.json();
console.log(result.data.permissions); // Manager permissions applied
```

### Workflow 3: Custom Permissions Override

```javascript
// Override specific permissions without changing role
const response = await fetch('/api/team-members/3/update_permissions/', {
  method: 'PATCH',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    can_manage_documents: true,
    can_manage_transfers: true,
    can_manage_team: false
  })
});

const result = await response.json();
```

### Workflow 4: Search and Filter Team Members

```javascript
// Search for team members
const response = await fetch('/api/team-members/?search=mason&role=manager&is_active=true', {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});

const teamMembers = await response.json();
```

### Workflow 5: Toggle RBAC Setting

```javascript
// Enable/disable role-based access controls
const response = await fetch('/api/syndicate/settings/team-management/', {
  method: 'PATCH',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    enable_role_based_access_controls: true
  })
});

const result = await response.json();
console.log(result.message);
```

---

## Error Responses

### Not Authenticated
```json
{
  "detail": "Authentication credentials were not provided."
}
```
**Status:** 401 Unauthorized

### Permission Denied
```json
{
  "detail": "You do not have permission to perform this action."
}
```
**Status:** 403 Forbidden

### Team Member Already Exists
```json
{
  "email": ["A team member with this email already exists."]
}
```
**Status:** 400 Bad Request

### Team Member Not Found
```json
{
  "detail": "Not found."
}
```
**Status:** 404 Not Found

---

## Data Model

### TeamMember Fields

```python
# Basic Info
name = CharField(max_length=255)
email = EmailField()
syndicate = ForeignKey(SyndicateProfile)
user = ForeignKey(CustomUser, null=True)  # If registered

# Role
role = CharField(choices=ROLE_CHOICES)
# Choices: manager, analyst, associate, partner, admin, viewer

# Permissions
can_access_dashboard = BooleanField(default=True)
can_manage_spvs = BooleanField(default=False)
can_manage_documents = BooleanField(default=False)
can_manage_investors = BooleanField(default=False)
can_view_reports = BooleanField(default=True)
can_manage_transfers = BooleanField(default=False)
can_manage_team = BooleanField(default=False)
can_manage_settings = BooleanField(default=False)

# Status
is_active = BooleanField(default=True)
invitation_sent = BooleanField(default=False)
invitation_accepted = BooleanField(default=False)

# Metadata
added_by = ForeignKey(CustomUser)
added_at = DateTimeField(auto_now_add=True)
updated_at = DateTimeField(auto_now=True)
```

---

## UI Integration Tips (Based on Figma)

1. **Team Member Cards**: Display name, role badge, and permission dropdowns
2. **Role Dropdown**: Use `/team-members/roles/` to populate role options
3. **Permission Dropdowns**: Use `/team-members/permissions_list/` for labels
4. **Search Bar**: Use `?search=` parameter for real-time search
5. **Pagination**: Built-in with page numbers (1, 2, 3, 4...)
6. **Action Buttons**: Eye icon (view), three dots (actions menu)
7. **Add New Members Button**: Opens modal with POST `/team-members/`
8. **Save Changes**: Updates only modified team members
9. **RBAC Toggle**: Use settings endpoint to enable/disable
10. **Visual Indicators**: Show registered vs invited members differently

---

## Summary

The Team Management API provides:
- ✅ Complete team member CRUD operations
- ✅ Role-based access control (RBAC) system
- ✅ Individual permission overrides
- ✅ 6 predefined roles with permission matrices
- ✅ Search and filtering capabilities
- ✅ Team statistics and analytics
- ✅ Activation/deactivation support
- ✅ Invitation tracking (for future email invitations)
- ✅ Comprehensive permission management
- ✅ Integration with syndicate settings

Perfect for managing team collaboration with granular access control! 👥🔐
