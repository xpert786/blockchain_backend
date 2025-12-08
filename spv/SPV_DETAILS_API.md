# SPV Details API Documentation

Complete API endpoints for viewing detailed SPV information including metrics, terms, investors, and documents.

## Base URL
```
/api/spv/
```

---

## 1. SPV Details Endpoint

**Endpoint:** `GET /api/spv/{spv_id}/details/`

**Description:** Get comprehensive details about a specific SPV including financial metrics, terms, company info, and documents.

**Authentication:** Required (Bearer Token)

**Parameters:**
- `spv_id` (integer, required): The SPV ID

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "spv_code": "SPV-001",
    "display_name": "Tech Startup Fund Q4 2024",
    "status": "active",
    "status_label": "Active",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-11-28T14:20:00Z",
    
    "spv_details": {
      "spv_code": "SPV-001",
      "year": 2024,
      "country": "Delaware, USA",
      "incorporation_date": "01/15/2024",
      "term_length_years": 7,
      "fund_lead": {
        "id": 5,
        "name": "John Doe",
        "email": "john@example.com"
      },
      "jurisdiction": "Delaware"
    },
    
    "financial_metrics": {
      "total_value": 2400000,
      "uninvested_sum": 300000,
      "irr": 15.2,
      "multiple": 1.7
    },
    
    "fundraising_progress": {
      "my_spvs": 2400000,
      "target": 5000000,
      "gp_commitment": 250000,
      "total_raised": 2650000,
      "progress_percent": 53.0,
      "remaining_amount": 2350000,
      "target_closing_date": "2024-12-31",
      "days_to_close": 33
    },
    
    "investment_terms": {
      "minimum_investment": 25000,
      "valuation_type": "pre_money",
      "valuation_type_label": "Pre money",
      "instrument_type": "SAFE",
      "share_class": "Series A",
      "round": "Series A",
      "transaction_type": "primary",
      "transaction_type_label": "Primary"
    },
    
    "portfolio_company": {
      "name": "Tech StartUp Inc",
      "stage": "Series A",
      "sector": "Technology",
      "sectors": ["Technology", "AI", "SaaS"]
    },
    
    "carry_fees": {
      "total_carry_percentage": 20.0,
      "lead_carry_percentage": 5.0,
      "carry_recipient": "Fund Manager LLC"
    },
    
    "investors": {
      "count": 24,
      "emails": ["investor1@example.com", "investor2@example.com", ...]
    },
    
    "documents": {
      "pitch_deck_url": "https://example.com/media/spv/pitch_decks/tech-startup.pdf",
      "supporting_document_url": "https://example.com/media/spv/supporting_documents/term-sheet.pdf",
      "deal_memo": "This is a Series A investment in a technology company..."
    },
    
    "additional_info": {
      "deal_name": "Tech Innovation Fund",
      "adviser_entity": "platform_advisers",
      "master_partnership_entity": "Platform Partners LLC",
      "access_mode": "private",
      "investment_visibility": "visible",
      "deal_partners": "Strategic Partner Inc, Tech Advisors LLC",
      "founder_email": "founder@company.com"
    }
  }
}
```

**Status Codes:**
- `200 OK`: Successfully retrieved SPV details
- `403 Forbidden`: User doesn't have access to this SPV
- `404 Not Found`: SPV not found

---

## 2. Performance Metrics Endpoint

**Endpoint:** `GET /api/spv/{spv_id}/performance-metrics/`

**Description:** Get performance metrics for an SPV including total value, returns, and quarterly data.

**Authentication:** Required

**Parameters:**
- `spv_id` (integer, required): The SPV ID

**Response:**
```json
{
  "success": true,
  "data": {
    "spv_id": 1,
    "spv_name": "Tech Startup Fund Q4 2024",
    "performance": {
      "total_value": 2400000,
      "uninvested_sum": 0,
      "irr": 15.2,
      "multiple": 1.7,
      "return_percent": 70.0
    },
    "quarterly_data": [
      {
        "quarter": "Q1 2024",
        "value": 2400000,
        "benchmark": 2400000
      },
      {
        "quarter": "Q2 2024",
        "value": 1398000,
        "benchmark": 1221000
      },
      {
        "quarter": "Q3 2024",
        "value": 9800000,
        "benchmark": 2290000
      },
      {
        "quarter": "Q4 2024",
        "value": 3908000,
        "benchmark": 2000000
      }
    ]
  }
}
```

**Metrics Definitions:**
- `total_value`: Total investment value in the SPV
- `uninvested_sum`: Remaining uninvested amount
- `irr`: Internal Rate of Return (%)
- `multiple`: Return multiple (X times)
- `return_percent`: Total return percentage

---

## 3. Investment Terms Endpoint

**Endpoint:** `GET /api/spv/{spv_id}/investment-terms/`

**Description:** Get detailed investment terms for an SPV including minimum investment, valuation, instruments, and carry details.

**Authentication:** Required

**Parameters:**
- `spv_id` (integer, required): The SPV ID

**Response:**
```json
{
  "success": true,
  "data": {
    "spv_id": 1,
    "spv_name": "Tech Startup Fund Q4 2024",
    "minimum_investment": {
      "amount": 25000,
      "currency": "USD"
    },
    "valuation": {
      "type": "pre_money",
      "type_label": "Pre money",
      "amount": 5000000
    },
    "instrument": {
      "type": "SAFE",
      "description": "Simple Agreement for Future Equity"
    },
    "round": {
      "name": "Series A",
      "description": "Series A Funding Round"
    },
    "share_class": {
      "name": "Series A Preferred",
      "description": "Series A Preferred Stock"
    },
    "carry": {
      "total_carry_percentage": 20.0,
      "lead_carry_percentage": 5.0,
      "carry_recipient": "Fund Manager LLC"
    },
    "transaction": {
      "type": "primary",
      "type_label": "Primary"
    },
    "target_closing_date": "2024-12-31"
  }
}
```

---

## 4. Investors List Endpoint

**Endpoint:** `GET /api/spv/{spv_id}/investors/`

**Description:** Get list of all investors in an SPV with their investment details.

**Authentication:** Required

**Parameters:**
- `spv_id` (integer, required): The SPV ID
- `page` (integer, optional): Page number for pagination (default: 1)
- `page_size` (integer, optional): Number of results per page (default: 10)

**Response:**
```json
{
  "success": true,
  "data": {
    "spv_id": 1,
    "spv_name": "Tech Startup Fund Q4 2024",
    "total_investors": 24,
    "total_raised": 2650000,
    "investors": [
      {
        "name": "Michael Investor",
        "email": "michael@example.com",
        "amount": 50000,
        "percentage": 25,
        "date": "09/28/2025",
        "status": "Active"
      },
      {
        "name": "Sarah Johnson",
        "email": "sarah@example.com",
        "amount": 50000,
        "percentage": 25,
        "date": "09/28/2025",
        "status": "Active"
      },
      {
        "name": "Michael Investor",
        "email": "michael2@example.com",
        "amount": 50000,
        "percentage": 25,
        "date": "09/28/2025",
        "status": "Active"
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 3,
      "page_size": 10,
      "total_count": 24
    }
  }
}
```

**Investor Fields:**
- `name`: Investor name
- `email`: Investor email address
- `amount`: Investment amount in USD
- `percentage`: Ownership percentage
- `date`: Investment date (MM/DD/YYYY)
- `status`: Investment status (Active, Pending, Withdrawn, etc.)

---

## 5. Documents Endpoint

**Endpoint:** `GET /api/spv/{spv_id}/documents/`

**Description:** Get all documents associated with an SPV (pitch deck, supporting documents, etc.).

**Authentication:** Required

**Parameters:**
- `spv_id` (integer, required): The SPV ID

**Response:**
```json
{
  "success": true,
  "data": {
    "spv_id": 1,
    "spv_name": "Tech Startup Fund Q4 2024",
    "total_documents": 2,
    "documents": [
      {
        "id": 1,
        "name": "Pitch Deck",
        "type": "presentation",
        "url": "https://example.com/media/spv/pitch_decks/tech-startup.pdf",
        "uploaded_at": "2024-01-15T10:30:00Z",
        "uploaded_by": "John Doe",
        "size_mb": 5.2
      },
      {
        "id": 2,
        "name": "Supporting Document",
        "type": "document",
        "url": "https://example.com/media/spv/supporting_documents/term-sheet.pdf",
        "uploaded_at": "2024-11-28T14:20:00Z",
        "uploaded_by": "John Doe",
        "size_mb": 3.1
      }
    ]
  }
}
```

**Document Fields:**
- `id`: Document ID
- `name`: Document name
- `type`: Document type (presentation, document, etc.)
- `url`: Direct URL to download document
- `uploaded_at`: Upload timestamp
- `uploaded_by`: Name of person who uploaded
- `size_mb`: File size in MB

---

## Error Responses

### 403 Forbidden
```json
{
  "error": "You do not have permission to access this SPV"
}
```

### 404 Not Found
```json
{
  "error": "Not found."
}
```

---

## Usage Examples

### Get SPV Details
```bash
curl -X GET "https://api.example.com/api/spv/1/details/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

### Get SPV Performance Metrics
```bash
curl -X GET "https://api.example.com/api/spv/1/performance-metrics/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get SPV Investment Terms
```bash
curl -X GET "https://api.example.com/api/spv/1/investment-terms/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get SPV Investors
```bash
curl -X GET "https://api.example.com/api/spv/1/investors/?page=1&page_size=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get SPV Documents
```bash
curl -X GET "https://api.example.com/api/spv/1/documents/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Authorization

All endpoints require JWT Bearer token authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

Users can only access SPVs they created or are admins. Attempting to access another user's SPV will result in a 403 Forbidden response.

---

## Response Status Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request |
| 403 | Forbidden - No permission to access |
| 404 | Not Found - SPV doesn't exist |
| 500 | Server Error |

---

## Notes

- All monetary amounts are in USD
- Percentages are expressed as decimal numbers (e.g., 20.0 for 20%)
- Dates are in ISO 8601 format
- Pagination is optional; defaults to 1 page with 10 items
- Document URLs are absolute paths and can be accessed directly
- Performance metrics (IRR, Multiple) are placeholder values and should be calculated from actual portfolio data

