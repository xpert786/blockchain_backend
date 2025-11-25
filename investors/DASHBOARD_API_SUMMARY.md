# Dashboard API Quick Reference

## Overview
Complete dashboard, portfolio, investment, and notification APIs for the Unlocksley platform.

## Base URLs
- **Investor Onboarding**: `/blockchain-backend/api/profiles/`
- **Dashboard**: `/blockchain-backend/api/dashboard/`
- **Portfolio**: `/blockchain-backend/api/portfolio/`
- **Investments**: `/blockchain-backend/api/investments/`
- **Notifications**: `/blockchain-backend/api/notifications/`

## Authentication
All endpoints require JWT authentication:
```
Authorization: Bearer <your_jwt_token>
```

---

## Quick Access Endpoints

### Dashboard Overview
```
GET /blockchain-backend/api/dashboard/overview/
```
Returns: KYC status, portfolio summary, recent investments, notification counts

### My Portfolio
```
GET /blockchain-backend/api/portfolio/my_portfolio/
```
Returns: Complete portfolio with all investments and performance metrics

### My Investments
```
GET /blockchain-backend/api/investments/my_investments/
GET /blockchain-backend/api/investments/active/
GET /blockchain-backend/api/investments/pending/
GET /blockchain-backend/api/investments/by_type/?type=syndicate_deal
```
Filter by: investment_type, sector, status

### My Notifications
```
GET /blockchain-backend/api/notifications/my_notifications/
GET /blockchain-backend/api/notifications/unread/
GET /blockchain-backend/api/notifications/action_required/
GET /blockchain-backend/api/notifications/stats/
```
Filter by: type, status, priority, action_required

### Notification Actions
```
POST /blockchain-backend/api/notifications/{id}/mark_read/
POST /blockchain-backend/api/notifications/mark_all_read/
DELETE /blockchain-backend/api/notifications/clear_all/
```

---

## Models Created

### Portfolio
- Tracks total invested, current value, unrealized gains
- Auto-calculates growth percentages
- Links to all user investments

### Investment
- Individual investment details
- Supports: Syndicate Deals, Top Syndicates, Invites
- Auto-calculates gain/loss percentages
- Status: pending, active, completed, cancelled

### Notification
- Types: investment, document, transfer, system
- Priority: low, medium, high, urgent
- Action required flagging
- Read/unread status tracking

### KYCStatus
- Tracks KYC verification process
- Status: pending, under_review, approved, rejected
- Reviewer notes and timestamps

---

## Testing

### Using cURL
```bash
# Get dashboard overview
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/blockchain-backend/api/dashboard/overview/

# Get portfolio
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/blockchain-backend/api/portfolio/my_portfolio/

# Get investments
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/blockchain-backend/api/investments/my_investments/

# Get notifications
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/blockchain-backend/api/notifications/my_notifications/
```

### Using Python
```python
import requests

TOKEN = "your_jwt_token"
headers = {"Authorization": f"Bearer {TOKEN}"}

# Get dashboard
response = requests.get(
    "http://localhost:8000/blockchain-backend/api/dashboard/overview/",
    headers=headers
)
dashboard = response.json()

# Get portfolio
response = requests.get(
    "http://localhost:8000/blockchain-backend/api/portfolio/my_portfolio/",
    headers=headers
)
portfolio = response.json()
```

---

## Admin Interface

Access at: `http://localhost:8000/blockchain-backend/admin/`

### Available Admin Pages
- **Investor Profiles**: View and manage all investor applications
- **Portfolios**: Track portfolio values and performance
- **Investments**: Manage individual investments with bulk actions
- **Notifications**: Send and manage notifications (mark as read/unread)
- **KYC Status**: Review and approve KYC submissions

### Custom Admin Actions
- Mark investments as active/completed
- Mark notifications as read/unread
- Export data to CSV
- Bulk status updates

---

## Common Queries

### Filter Investments by Syndicate Type
```
GET /blockchain-backend/api/investments/by_type/?type=syndicate_deal
GET /blockchain-backend/api/investments/by_type/?type=top_syndicate
GET /blockchain-backend/api/investments/by_type/?type=invite
```

### Filter Notifications by Type
```
GET /blockchain-backend/api/notifications/my_notifications/?type=investment
GET /blockchain-backend/api/notifications/my_notifications/?type=document
GET /blockchain-backend/api/notifications/my_notifications/?type=transfer
GET /blockchain-backend/api/notifications/my_notifications/?type=system
```

### Get High Priority Action Items
```
GET /blockchain-backend/api/notifications/my_notifications/?priority=high&action_required=true
```

---

## Data Flow

1. **User Registration** → Creates CustomUser
2. **Onboarding (6 Steps)** → Creates InvestorProfile
3. **KYC Submission** → Creates KYCStatus
4. **KYC Approval** → Updates KYCStatus to approved
5. **Portfolio Creation** → Auto-created Portfolio on first investment
6. **Make Investment** → Creates Investment, updates Portfolio
7. **Notifications** → Created for important events
8. **Dashboard** → Aggregates all user data

---

## Performance Metrics

The Portfolio model automatically calculates:
- **Total Invested**: Sum of all investment amounts
- **Current Value**: Sum of all current investment values
- **Unrealized Gain**: Current value - Total invested
- **Growth %**: (Unrealized gain / Total invested) × 100
- **Investment Counts**: Total, active, pending investments

---

## Response Examples

### Dashboard Overview
```json
{
    "kyc_status": {
        "status": "approved",
        "submitted_at": "2024-01-15T10:30:00Z"
    },
    "portfolio_summary": {
        "total_invested": "500000.00",
        "current_value": "575000.00",
        "unrealized_gain": "75000.00",
        "portfolio_growth_percentage": "15.00"
    },
    "recent_investments": [...],
    "notification_summary": {
        "total_count": 15,
        "unread_count": 5,
        "action_required_count": 2
    }
}
```

### Investment Details
```json
{
    "id": 1,
    "syndicate_name": "Tech Ventures Fund",
    "sector": "technology",
    "investment_type": "syndicate_deal",
    "amount_invested": "100000.00",
    "current_value": "120000.00",
    "gain_loss": "20000.00",
    "gain_loss_percentage": "20.00",
    "status": "active"
}
```

---

## Next Steps

1. **Test All Endpoints**: Use Postman or curl to test each endpoint
2. **Create Sample Data**: Use Django admin to create test portfolios and investments
3. **Frontend Integration**: Connect React/Vue frontend to these APIs
4. **Add Real-time Updates**: Consider WebSockets for live portfolio updates
5. **Monitoring**: Set up logging and error tracking

---

## Support

- Full Documentation: [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
- Main README: [README.md](./README.md)
- Django Admin: http://localhost:8000/blockchain-backend/admin/
- API Root: http://localhost:8000/blockchain-backend/api/

For issues, contact the development team.
