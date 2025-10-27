# Syndicate Update Examples - Complete Guide

## Table of Contents
1. [Update Single Field](#update-single-field)
2. [Update Multiple Fields](#update-multiple-fields)
3. [Update All Fields (Full Update)](#update-all-fields)
4. [Field-Specific Examples](#field-specific-examples)
5. [Update with File Upload](#update-with-file-upload)
6. [PowerShell Examples](#powershell-examples)
7. [Python Examples](#python-examples)

---

## Update Single Field

### Update Description Only
```bash
curl -X PATCH http://127.0.0.1:8000/api/syndicates/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated syndicate description focusing on early-stage tech investments"
  }'
```

### Update Sector Only
```bash
curl -X PATCH http://127.0.0.1:8000/api/syndicates/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sector": "Technology, AI, Machine Learning, Blockchain, Fintech, Cybersecurity"
  }'
```

### Update Geography Only
```bash
curl -X PATCH http://127.0.0.1:8000/api/syndicates/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "geography": "North America, Europe, Asia-Pacific, Middle East"
  }'
```

---

## Update Multiple Fields

### Update Investment Details
```bash
curl -X PATCH http://127.0.0.1:8000/api/syndicates/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Premier technology investment syndicate",
    "sector": "Technology, AI, SaaS, Fintech",
    "geography": "Global",
    "accredited": "Yes"
  }'
```

### Update LP Network Information
```bash
curl -X PATCH http://127.0.0.1:8000/api/syndicates/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "lp_network": "Angel investors, Venture Capital firms, Family offices, High-net-worth individuals",
    "enable_lp_network": "Yes",
    "team_member": "John Manager (Managing Partner), Sarah Smith (Investment Analyst), Mike Johnson (Legal Counsel), Lisa Brown (Operations Manager)"
  }'
```

### Update Compliance Fields
```bash
curl -X PATCH http://127.0.0.1:8000/api/syndicates/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "Risk_Regulatory_Attestation": "This syndicate operates in compliance with SEC Regulation D, Rule 506(c). All investors must be accredited. Regular compliance audits conducted quarterly.",
    "jurisdictional_requirements": "United States (all 50 states), Canada, United Kingdom, European Union member states, Singapore, Hong Kong",
    "additional_compliance_policies": "Comprehensive KYC/AML policies enforced for all investors. Annual third-party audits. GDPR compliant data handling. Regular compliance training for all team members. Anti-fraud measures in place."
  }'
```

---

## Update All Fields (Full Update)

### Complete PUT Request
```bash
curl -X PUT http://127.0.0.1:8000/api/syndicates/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tech Ventures Syndicate",
    "manager": 1,
    "description": "A leading syndicate focused on early to growth-stage technology investments, specializing in AI, blockchain, and enterprise SaaS companies. We provide capital, expertise, and network access to promising startups.",
    "accredited": "Yes",
    "sector": "Technology, Artificial Intelligence, Machine Learning, Blockchain, Enterprise SaaS, Fintech, Cybersecurity, Cloud Computing",
    "geography": "North America (US, Canada), Europe (UK, Germany, France, Netherlands), Asia-Pacific (Singapore, Hong Kong, Australia)",
    "lp_network": "Angel investors, Venture Capital firms, Family offices, Corporate VCs, High-net-worth individuals, Institutional investors",
    "enable_lp_network": "Yes",
    "firm_name": "Tech Ventures Management LLC",
    "team_member": "John Manager (Managing Partner, 15 years experience), Sarah Smith (Investment Analyst, MBA Stanford), Mike Johnson (Legal Counsel, SEC specialist), Lisa Brown (Operations Manager, CFA)",
    "Risk_Regulatory_Attestation": "This syndicate operates under SEC Regulation D, Rule 506(c). All offerings are exclusively available to accredited investors. We maintain comprehensive compliance programs and conduct regular third-party audits. Our investment thesis and risk management framework are reviewed quarterly by our advisory board.",
    "jurisdictional_requirements": "Primary jurisdiction: United States (Delaware). Licensed to operate in all 50 US states, Canada (Ontario, British Columbia), United Kingdom (FCA registered), European Union (ESMA compliant), Singapore (MAS registered), Hong Kong (SFC registered). All operations comply with local securities laws.",
    "additional_compliance_policies": "1. Comprehensive KYC/AML procedures for all LPs. 2. Annual third-party compliance audits. 3. GDPR-compliant data handling and privacy policies. 4. Regular compliance training (quarterly) for all team members. 5. Anti-fraud and anti-corruption measures. 6. Whistleblower protection program. 7. Conflicts of interest disclosure policy. 8. Cybersecurity protocols and annual penetration testing. 9. Document retention policy (7 years minimum). 10. Regular regulatory filings and reporting."
  }'
```

---

## Field-Specific Examples

### 1. Name
```bash
curl -X PATCH http://127.0.0.1:8000/api/syndicates/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Tech Ventures Syndicate 2.0"}'
```

### 2. Manager (Change Manager)
```bash
curl -X PATCH http://127.0.0.1:8000/api/syndicates/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"manager": 2}'
```

### 3. Description
```bash
curl -X PATCH http://127.0.0.1:8000/api/syndicates/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "We invest in transformative technology companies that are reshaping industries. Our focus areas include artificial intelligence, blockchain technology, and enterprise software solutions. We typically invest $500K-$5M in Series A and B rounds."
  }'
```

### 4. Accredited Status
```bash
curl -X PATCH http://127.0.0.1:8000/api/syndicates/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"accredited": "Yes"}'
```

### 5. Sector
```bash
curl -X PATCH http://127.0.0.1:8000/api/syndicates/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sector": "Technology, AI/ML, Blockchain, DeFi, Enterprise SaaS, Fintech, Healthtech, Edtech, Cybersecurity, Cloud Infrastructure, DevOps, API Platforms"
  }'
```

### 6. Geography
```bash
curl -X PATCH http://127.0.0.1:8000/api/syndicates/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "geography": "Global with primary focus on: North America (US, Canada), Western Europe (UK, Germany, France, Netherlands, Switzerland), Asia-Pacific (Singapore, Hong Kong, Australia, Japan), Emerging markets (India, Brazil, UAE)"
  }'
```

### 7. LP Network
```bash
curl -X PATCH http://127.0.0.1:8000/api/syndicates/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "lp_network": "Our LP network includes 200+ accredited investors: Angel investors (40%), Venture Capital firms (25%), Family offices (20%), Corporate VCs (10%), Institutional investors (5%). Total committed capital: $50M+"
  }'
```

### 8. Enable LP Network
```bash
curl -X PATCH http://127.0.0.1:8000/api/syndicates/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"enable_lp_network": "Yes"}'
```

Or disable:
```bash
curl -X PATCH http://127.0.0.1:8000/api/syndicates/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"enable_lp_network": "No"}'
```

### 9. Firm Name
```bash
curl -X PATCH http://127.0.0.1:8000/api/syndicates/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"firm_name": "Tech Ventures Management LLC"}'
```

### 10. Team Member
```bash
curl -X PATCH http://127.0.0.1:8000/api/syndicates/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "team_member": "John Manager (Managing Partner - 15 years VC experience, former Goldman Sachs), Sarah Smith (Principal - MBA Stanford, ex-Google PM), Mike Johnson (General Counsel - JD Harvard, SEC compliance expert), Lisa Brown (CFO - CPA, CFA, 20 years finance), David Lee (Venture Partner - Serial entrepreneur, 3 exits), Emma Wilson (Investment Associate - MIT Computer Science)"
  }'
```

### 11. Risk Regulatory Attestation
```bash
curl -X PATCH http://127.0.0.1:8000/api/syndicates/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "Risk_Regulatory_Attestation": "REGULATORY COMPLIANCE: This syndicate operates under SEC Regulation D, Rule 506(c), restricting participation to accredited investors only. We are registered with the SEC (File No. XXX-XXXXX) and maintain all required compliance documentation. \n\nRISK DISCLOSURE: Investments in early-stage companies carry substantial risk of loss. Past performance does not guarantee future results. Investors may lose their entire investment. Securities are illiquid and may not be readily transferable. \n\nAUDIT & OVERSIGHT: Annual audits conducted by Big 4 accounting firm. Quarterly compliance reviews. Monthly NAV calculations. Regular regulatory reporting to SEC."
  }'
```

### 12. Jurisdictional Requirements
```bash
curl -X PATCH http://127.0.0.1:8000/api/syndicates/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jurisdictional_requirements": "PRIMARY JURISDICTION: Delaware, USA (DE File No: XXXXX) | SEC REGISTRATION: Investment Adviser (File No: 801-XXXXX) | US STATES: Licensed in all 50 states + DC | CANADA: Ontario (OSC), British Columbia (BCSC) | UK: FCA Authorized (FRN: XXXXXX) | EU: MiFID II compliant, ESMA registered | SINGAPORE: MAS Licensed (CMS No: XXXXX) | HONG KONG: SFC Licensed (Type 9) | AUSTRALIA: AFSL holder | Tax jurisdictions: US (EIN: XX-XXXXXXX), UK, Singapore"
  }'
```

### 13. Additional Compliance Policies
```bash
curl -X PATCH http://127.0.0.1:8000/api/syndicates/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "additional_compliance_policies": "COMPLIANCE FRAMEWORK:\n\n1. KYC/AML PROGRAM: Enhanced due diligence for all LPs. Sanctions screening (OFAC, UN, EU). Source of funds verification. Ongoing monitoring. PEP screening.\n\n2. ANTI-BRIBERY & CORRUPTION: Zero tolerance policy. Annual training. Third-party due diligence. Gifts and entertainment policy.\n\n3. DATA PROTECTION: GDPR compliant. SOC 2 Type II certified. Annual penetration testing. Encryption at rest and in transit. Data retention policy (7 years).\n\n4. CONFLICTS OF INTEREST: Written disclosure policy. Pre-clearance for personal investments. Related party transaction approval process.\n\n5. TRAINING: Quarterly compliance training. Annual ethics certification. Specialized training for investment team.\n\n6. REPORTING: Quarterly LP reports. Annual audited financials. Monthly NAV updates. Regulatory filings (Form ADV, Form D, etc.).\n\n7. GOVERNANCE: Independent advisory board. Annual compliance audit. Whistleblower hotline. Regular policy reviews.\n\n8. CYBERSECURITY: Multi-factor authentication. Regular security audits. Incident response plan. Cyber insurance coverage.\n\n9. RECORD KEEPING: 7-year document retention. Secure cloud storage. Audit trail for all transactions.\n\n10. REGULATORY MONITORING: Dedicated compliance officer. Regulatory change monitoring. Legal counsel on retainer."
  }'
```

---

## Update with File Upload

### Upload Logo
```bash
curl -X PATCH http://127.0.0.1:8000/api/syndicates/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "logo=@/path/to/logo.png"
```

### Upload Logo with Other Fields
```bash
curl -X PATCH http://127.0.0.1:8000/api/syndicates/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "logo=@/path/to/logo.png" \
  -F "name=Tech Ventures Syndicate" \
  -F "description=Updated description" \
  -F "sector=Technology, AI"
```

---

## PowerShell Examples

### Basic Update
```powershell
$token = "YOUR_ACCESS_TOKEN"
$syndicateId = 1

$data = @{
    description = "Updated description"
    sector = "Technology, AI, Blockchain"
    geography = "Global"
} | ConvertTo-Json

$response = Invoke-RestMethod `
    -Uri "http://127.0.0.1:8000/api/syndicates/$syndicateId/" `
    -Method Patch `
    -Headers @{
        "Authorization" = "Bearer $token"
        "Content-Type" = "application/json"
    } `
    -Body $data

$response | ConvertTo-Json
```

### Update Multiple Syndicates (Loop)
```powershell
$token = "YOUR_ACCESS_TOKEN"
$syndicateIds = @(1, 2, 3)

foreach ($id in $syndicateIds) {
    $data = @{
        Risk_Regulatory_Attestation = "Updated compliance text"
        additional_compliance_policies = "Updated policies"
    } | ConvertTo-Json
    
    Write-Host "Updating syndicate $id..."
    
    $response = Invoke-RestMethod `
        -Uri "http://127.0.0.1:8000/api/syndicates/$id/" `
        -Method Patch `
        -Headers @{
            "Authorization" = "Bearer $token"
            "Content-Type" = "application/json"
        } `
        -Body $data
    
    Write-Host "✅ Syndicate $id updated successfully"
}
```

### Comprehensive Update
```powershell
$token = "YOUR_ACCESS_TOKEN"
$syndicateId = 1

$updateData = @{
    name = "Tech Ventures Syndicate"
    description = "Premier technology investment syndicate"
    accredited = "Yes"
    sector = "Technology, AI, Blockchain, SaaS, Fintech"
    geography = "North America, Europe, Asia"
    lp_network = "Angel investors, VCs, Family offices"
    enable_lp_network = "Yes"
    firm_name = "Tech Ventures LLC"
    team_member = "John Manager, Sarah Smith, Mike Johnson"
    Risk_Regulatory_Attestation = "SEC Regulation D compliant. Accredited investors only."
    jurisdictional_requirements = "US (all states), Canada, UK, EU, Singapore"
    additional_compliance_policies = "KYC/AML enforced. Annual audits. GDPR compliant."
} | ConvertTo-Json

$response = Invoke-RestMethod `
    -Uri "http://127.0.0.1:8000/api/syndicates/$syndicateId/" `
    -Method Patch `
    -Headers @{
        "Authorization" = "Bearer $token"
        "Content-Type" = "application/json"
    } `
    -Body $updateData

Write-Host "✅ Syndicate updated successfully!" -ForegroundColor Green
$response | ConvertTo-Json
```

---

## Python Examples

### Using Requests Library
```python
import requests
import json

# Configuration
BASE_URL = "http://127.0.0.1:8000/api"
TOKEN = "YOUR_ACCESS_TOKEN"
SYNDICATE_ID = 1

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Update single field
data = {
    "description": "Updated description from Python"
}

response = requests.patch(
    f"{BASE_URL}/syndicates/{SYNDICATE_ID}/",
    headers=headers,
    json=data
)

print(f"Status: {response.status_code}")
print(json.dumps(response.json(), indent=2))
```

### Update Multiple Fields
```python
import requests

BASE_URL = "http://127.0.0.1:8000/api"
TOKEN = "YOUR_ACCESS_TOKEN"
SYNDICATE_ID = 1

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

update_data = {
    "description": "Comprehensive tech investment syndicate",
    "sector": "Technology, AI, Blockchain, SaaS, Fintech, Cybersecurity",
    "geography": "North America, Europe, Asia-Pacific",
    "lp_network": "200+ accredited investors including VCs, angels, family offices",
    "enable_lp_network": "Yes",
    "team_member": "John Manager (GP), Sarah Smith (Principal), Mike Johnson (Counsel)",
    "Risk_Regulatory_Attestation": "SEC Reg D 506(c) compliant. Accredited investors only. Annual audits conducted.",
    "jurisdictional_requirements": "US (all states), Canada, UK, EU, Singapore, Hong Kong",
    "additional_compliance_policies": "KYC/AML enforced. GDPR compliant. SOC 2 certified. Quarterly compliance reviews."
}

response = requests.patch(
    f"{BASE_URL}/syndicates/{SYNDICATE_ID}/",
    headers=headers,
    json=update_data
)

if response.status_code == 200:
    print("✅ Syndicate updated successfully!")
    print(json.dumps(response.json(), indent=2))
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)
```

### Bulk Update Script
```python
import requests
import json

BASE_URL = "http://127.0.0.1:8000/api"
TOKEN = "YOUR_ACCESS_TOKEN"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Get all syndicates
response = requests.get(f"{BASE_URL}/syndicates/", headers=headers)
syndicates = response.json()['results']

# Update each syndicate
for syndicate in syndicates:
    syndicate_id = syndicate['id']
    
    update_data = {
        "additional_compliance_policies": "Updated compliance policies for all syndicates"
    }
    
    response = requests.patch(
        f"{BASE_URL}/syndicates/{syndicate_id}/",
        headers=headers,
        json=update_data
    )
    
    if response.status_code == 200:
        print(f"✅ Updated syndicate {syndicate_id}: {syndicate['name']}")
    else:
        print(f"❌ Failed to update syndicate {syndicate_id}")
```

---

## Common Update Scenarios

### Scenario 1: Initial Setup (Empty to Complete)
```bash
# Start with basic syndicate, then update with all details
curl -X PATCH http://127.0.0.1:8000/api/syndicates/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Complete description added",
    "sector": "Technology, AI, Blockchain",
    "geography": "North America, Europe",
    "lp_network": "Angel investors, VCs",
    "enable_lp_network": "Yes",
    "team_member": "Full team roster",
    "Risk_Regulatory_Attestation": "Full compliance details",
    "jurisdictional_requirements": "All jurisdictions listed",
    "additional_compliance_policies": "Complete policy documentation"
  }'
```

### Scenario 2: Quarterly Compliance Update
```bash
curl -X PATCH http://127.0.0.1:8000/api/syndicates/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "Risk_Regulatory_Attestation": "Q4 2024 Update: All compliance requirements met. Annual audit completed by KPMG on Dec 15, 2024. No material findings.",
    "additional_compliance_policies": "Updated Q4 2024: New cybersecurity protocols implemented. All team members completed annual compliance training."
  }'
```

### Scenario 3: Team Changes
```bash
curl -X PATCH http://127.0.0.1:8000/api/syndicates/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "team_member": "John Manager (Managing Partner), Sarah Smith (Principal - Promoted), Mike Johnson (General Counsel), David Lee (New Venture Partner - joined Jan 2025)"
  }'
```

### Scenario 4: Expansion to New Markets
```bash
curl -X PATCH http://127.0.0.1:8000/api/syndicates/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "geography": "North America, Europe, Asia-Pacific, Middle East (EXPANDED)",
    "jurisdictional_requirements": "Added: UAE (DIFC registered), Saudi Arabia (CMA licensed), India (SEBI registered)"
  }'
```

---

## Response Examples

### Successful Update (200 OK)
```json
{
  "id": 1,
  "name": "Tech Ventures Syndicate",
  "manager": 1,
  "manager_username": "syndicate_manager",
  "description": "Updated description",
  "accredited": "Yes",
  "sector": "Technology, AI, Blockchain",
  "geography": "Global",
  "lp_network": "Updated LP network",
  "enable_lp_network": "Yes",
  "firm_name": "Tech Ventures LLC",
  "logo": null,
  "team_member": "Updated team",
  "Risk_Regulatory_Attestation": "Updated attestation",
  "jurisdictional_requirements": "Updated requirements",
  "additional_compliance_policies": "Updated policies"
}
```

### Validation Error (400 Bad Request)
```json
{
  "accredited": ["Invalid choice. Must be 'Yes' or 'No'."]
}
```

### Unauthorized (401)
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### Not Found (404)
```json
{
  "detail": "Not found."
}
```

---

## Tips & Best Practices

1. **Use PATCH for partial updates** - Only send fields you want to change
2. **Use PUT for complete replacement** - Must send all required fields
3. **Validate data before sending** - Check field formats and constraints
4. **Keep token secure** - Never expose in logs or version control
5. **Handle errors gracefully** - Check response status codes
6. **Update incrementally** - Test with single fields first
7. **Backup before bulk updates** - Always have a rollback plan
8. **Use version control** - Track changes to compliance docs
9. **Log all updates** - Maintain audit trail
10. **Test in development** - Never test on production data

---

## Quick Reference

| Method | Endpoint | Purpose |
|--------|----------|---------|
| PATCH | `/api/syndicates/{id}/` | Update specific fields |
| PUT | `/api/syndicates/{id}/` | Replace entire record |
| GET | `/api/syndicates/{id}/` | View current values |
| DELETE | `/api/syndicates/{id}/` | Delete syndicate |

---

**Happy Updating! 🚀**


