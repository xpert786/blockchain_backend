# Team Management API - Quick Reference

## Base URLs
- Team Members: `/api/team-members/`
- Settings: `/api/syndicate/settings/team-management/`

## Endpoints Summary

### CRUD Operations
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/team-members/` | List all team members |
| `POST` | `/api/team-members/` | Add new team member |
| `GET` | `/api/team-members/{id}/` | Get team member details |
| `PATCH` | `/api/team-members/{id}/` | Update team member |
| `DELETE` | `/api/team-members/{id}/` | Remove team member |

### Role & Permission Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| `PATCH` | `/api/team-members/{id}/update_role/` | Update role (with auto-permissions) |
| `PATCH` | `/api/team-members/{id}/update_permissions/` | Update specific permissions |

### Status Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/team-members/{id}/activate/` | Activate team member |
| `POST` | `/api/team-members/{id}/deactivate/` | Deactivate team member |

### Metadata & Utilities
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/team-members/roles/` | Get available roles |
| `GET` | `/api/team-members/permissions_list/` | Get available permissions |
| `GET` | `/api/team-members/statistics/` | Get team statistics |

### Settings Integration
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/syndicate/settings/team-management/` | Get team overview + RBAC setting |
| `PATCH` | `/api/syndicate/settings/team-management/` | Update RBAC setting |

---

## Available Roles

1. **Manager** - Full access to everything
2. **Partner** - Access to SPVs, documents, investors, transfers, reports
3. **Admin** - Same as Manager
4. **Associate** - Access to dashboard, documents, investors, reports
5. **Analyst** - Access to dashboard, documents, reports
6. **Viewer** - Read-only access to dashboard and reports

---

## Available Permissions

1. `can_access_dashboard` - Access Dashboard
2. `can_manage_spvs` - Manage SPVs
3. `can_manage_documents` - Manage Documents
4. `can_manage_investors` - Manage Investors
5. `can_view_reports` - View Reports
6. `can_manage_transfers` - Manage Transfers
7. `can_manage_team` - Manage Team
8. `can_manage_settings` - Manage Settings

---

## Quick Examples

### Add Team Member
```bash
POST /api/team-members/
{
  "name": "Carter Jack",
  "email": "carter@example.com",
  "role": "analyst"
}
```

### Update Role
```bash
PATCH /api/team-members/2/update_role/
{
  "role": "manager",
  "apply_role_permissions": true
}
```

### Update Permissions
```bash
PATCH /api/team-members/2/update_permissions/
{
  "can_manage_documents": true,
  "can_manage_team": false
}
```

### Search Team Members
```bash
GET /api/team-members/?search=mason&role=manager&is_active=true
```

### Enable RBAC
```bash
PATCH /api/syndicate/settings/team-management/
{
  "enable_role_based_access_controls": true
}
```

---

## Query Parameters (List Endpoint)

- `search` - Search by name, email, or role
- `role` - Filter by role (manager, analyst, etc.)
- `is_active` - Filter by active status (true/false)

---

## Response Format

### Success Response
```json
{
  "message": "Operation successful",
  "data": { ... }
}
```

### List Response
```json
[
  {
    "id": 1,
    "name": "Mason Harper",
    "email": "mason@example.com",
    "role": "manager",
    "is_active": true
  }
]
```

### Error Response
```json
{
  "error": "Error message"
}
```
or
```json
{
  "field_name": ["Validation error message"]
}
```

---

## Authentication

All endpoints require JWT authentication:
```
Authorization: Bearer YOUR_JWT_TOKEN
```

## Permissions

- Syndicate owner: Full access
- Team member with `can_manage_team=True`: Can manage team
- Others: No access

---

## Integration with Figma Design

**Screen 36 - Team Management** maps to:
- Search bar → `?search=` parameter
- Team member cards → List endpoint
- Role dropdown → Update role endpoint
- Permissions dropdown → Update permissions endpoint
- Add button → Create endpoint
- Eye icon → View details endpoint
- Three dots menu → Actions (activate/deactivate/delete)
- Save button → Batch update multiple members
- Pagination → Built-in DRF pagination

---

## Files Created

1. `users/models.py` - TeamMember model (170+ lines)
2. `users/serializers.py` - 6 team member serializers (150+ lines)
3. `users/team_management_views.py` - Complete ViewSet (300+ lines)
4. `users/admin.py` - Admin interface for team members
5. `users/urls.py` - Router configuration
6. `users/migrations/0003_teammember.py` - Database migration
7. `users/TEAM_MANAGEMENT_API.md` - Full documentation (600+ lines)

---

## Database Model

**Table:** `users_teammember`

**Key Fields:**
- `syndicate_id` (FK to SyndicateProfile)
- `user_id` (FK to CustomUser, nullable)
- `name`, `email`
- `role` (6 choices)
- 8 permission boolean fields
- `is_active`, `invitation_sent`, `invitation_accepted`
- `added_by_id`, `added_at`, `updated_at`

**Unique Constraint:** `(syndicate_id, email)`

---

## Testing Checklist

- [x] Model created with all fields
- [x] Migrations applied successfully
- [x] Serializers handle all operations
- [x] ViewSet with CRUD operations
- [x] Role update endpoint
- [x] Permissions update endpoint
- [x] Activate/deactivate endpoints
- [x] Search and filter working
- [x] Statistics endpoint
- [x] Admin interface registered
- [x] URL routing configured
- [x] Permission checks in place
- [x] RBAC integration
- [x] Server check passed ✅

---

## Next Steps (Optional Enhancements)

1. **Email Invitations**: Send invitation emails to new team members
2. **Token-based Registration**: Allow invited members to register with token
3. **Notification System**: Notify when permissions change
4. **Audit Log**: Track who made changes to team members
5. **Bulk Operations**: Add/update/remove multiple members at once
6. **Export Feature**: Export team list to CSV/Excel
7. **Activity Tracking**: Track team member activities
8. **Permission Templates**: Save and apply permission templates

---

## Support

For issues or questions:
- Check full documentation: `TEAM_MANAGEMENT_API.md`
- Review model definitions: `users/models.py` (TeamMember class)
- Check serializers: `users/serializers.py`
- Review views: `users/team_management_views.py`
