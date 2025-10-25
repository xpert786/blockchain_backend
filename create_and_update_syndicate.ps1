# PowerShell script to create and update syndicate
$token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzYwMzU3MjU5LCJpYXQiOjE3NjAzMzkyNTksImp0aSI6IjBiMmQ4MDNjYmIxNzRlMzI5MDgwMjI0NTMwMTZjYmUwIiwidXNlcl9pZCI6IjUifQ.-G7G0IFpZBT0k-TcvY0pSTfxne5rMILKRojLrwc8aB0"
$baseUrl = "http://127.0.0.1:8000/api"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Syndicate Creation and Update Script" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

# Step 1: Check current user
Write-Host "`n1. Checking current user..." -ForegroundColor Yellow
try {
    $user = Invoke-RestMethod -Uri "$baseUrl/users/me/" -Headers @{"Authorization"="Bearer $token"}
    Write-Host "Logged in as: $($user.username) (ID: $($user.id))" -ForegroundColor Green
} catch {
    Write-Host "Error checking user: $($_.Exception.Message)" -ForegroundColor Red
    exit
}

# Step 2: List existing syndicates
Write-Host "`n2. Listing existing syndicates..." -ForegroundColor Yellow
try {
    $syndicates = Invoke-RestMethod -Uri "$baseUrl/syndicates/" -Headers @{"Authorization"="Bearer $token"}
    Write-Host "Found $($syndicates.count) syndicates:" -ForegroundColor Green
    foreach ($syn in $syndicates.results) {
        Write-Host "  - ID: $($syn.id), Name: $($syn.name)" -ForegroundColor Cyan
    }
} catch {
    Write-Host "Error listing syndicates: $($_.Exception.Message)" -ForegroundColor Red
}

# Step 3: Check if syndicate 7 exists
Write-Host "`n3. Checking if syndicate ID 7 exists..." -ForegroundColor Yellow
try {
    $syndicate7 = Invoke-RestMethod -Uri "$baseUrl/syndicates/7/" -Headers @{"Authorization"="Bearer $token"}
    Write-Host "Syndicate 7 exists: $($syndicate7.name)" -ForegroundColor Green
    $syndicateExists = $true
    $syndicateId = 7
} catch {
    Write-Host "Syndicate 7 does NOT exist" -ForegroundColor Yellow
    $syndicateExists = $false
}

# Step 4: Create or Update
if (-not $syndicateExists) {
    Write-Host "`n4. Creating new syndicate..." -ForegroundColor Yellow
    
    $createData = @{
        name = "syndicate_manager2"
        manager = $user.id
        description = "Complete update of all fields"
        accredited = "Yes"
        sector = "Technology, AI, Blockchain"
        geography = "North America"
        lp_network = "Angel investors, VCs"
        enable_lp_network = "Yes"
        firm_name = "Tech Ventures LLC"
        team_member = "John Manager, Sarah Smith"
        Risk_Regulatory_Attestation = "SEC compliant"
        jurisdictional_requirements = "US, Canada"
        additional_compliance_policies = "KYC/AML enforced"
    } | ConvertTo-Json
    
    try {
        $newSyndicate = Invoke-RestMethod -Uri "$baseUrl/syndicates/" -Method Post -Headers $headers -Body $createData
        Write-Host "Syndicate created successfully!" -ForegroundColor Green
        Write-Host "New Syndicate ID: $($newSyndicate.id)" -ForegroundColor Cyan
        Write-Host "Name: $($newSyndicate.name)" -ForegroundColor Cyan
        $syndicateId = $newSyndicate.id
    } catch {
        Write-Host "Error creating syndicate: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.ErrorDetails) {
            Write-Host "Details: $($_.ErrorDetails.Message)" -ForegroundColor Red
        }
        exit
    }
} else {
    Write-Host "`n4. Updating existing syndicate 7..." -ForegroundColor Yellow
    
    $updateData = @{
        name = "syndicate_manager2"
        manager = $user.id
        description = "Complete update of all fields"
        accredited = "Yes"
        sector = "Technology, AI, Blockchain"
        geography = "North America"
        lp_network = "Angel investors, VCs"
        enable_lp_network = "Yes"
        firm_name = "Tech Ventures LLC"
        team_member = "John Manager, Sarah Smith"
        Risk_Regulatory_Attestation = "SEC compliant"
        jurisdictional_requirements = "US, Canada"
        additional_compliance_policies = "KYC/AML enforced"
    } | ConvertTo-Json
    
    try {
        $updated = Invoke-RestMethod -Uri "$baseUrl/syndicates/7/" -Method Put -Headers $headers -Body $updateData
        Write-Host "Syndicate updated successfully!" -ForegroundColor Green
        Write-Host "Updated Syndicate ID: $($updated.id)" -ForegroundColor Cyan
        Write-Host "Name: $($updated.name)" -ForegroundColor Cyan
    } catch {
        Write-Host "Error updating syndicate: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.ErrorDetails) {
            Write-Host "Details: $($_.ErrorDetails.Message)" -ForegroundColor Red
        }
    }
}

# Step 5: Verify the result
Write-Host "`n5. Verifying syndicate details..." -ForegroundColor Yellow
try {
    $finalSyndicate = Invoke-RestMethod -Uri "$baseUrl/syndicates/$syndicateId/" -Headers @{"Authorization"="Bearer $token"}
    Write-Host "Final syndicate details:" -ForegroundColor Green
    $finalSyndicate | ConvertTo-Json | Write-Host
} catch {
    Write-Host "Error retrieving syndicate: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "Script Complete!" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

