param (
    [Parameter(Mandatory = $true)]
    [string]$CredentialsPath,

    [Parameter(Mandatory = $true)]
    [string]$AcrName
)

Write-Host "Reading AZURE_CREDENTIALS from: $CredentialsPath" -ForegroundColor Cyan

if (!(Test-Path $CredentialsPath)) {
    Write-Host "ERROR: Credentials file not found at $CredentialsPath" -ForegroundColor Red
    exit 1
}

# Parse JSON
$creds = Get-Content $CredentialsPath | ConvertFrom-Json
$clientId = $creds.clientId
$tenantId = $creds.tenantId
$subscriptionId = $creds.subscriptionId
$clientSecret = $creds.clientSecret

if (-not $clientId) {
    Write-Host "ERROR: Could not extract clientId from credentials file" -ForegroundColor Red
    exit 1
}

Write-Host "Service Principal Client ID: $clientId"
Write-Host "Subscription ID: $subscriptionId"
Write-Host "Tenant ID: $tenantId"

# Login to Azure
Write-Host "Logging in to Azure..."
az login --service-principal -u $clientId -p $clientSecret --tenant $tenantId | Out-Null
az account set --subscription $subscriptionId

# Validate ACR
$acr = az acr show -n $AcrName --query "id" -o tsv 2>$null
if (-not $acr) {
    Write-Host "ERROR: ACR $AcrName not found in subscription $subscriptionId" -ForegroundColor Red
    exit 1
}
Write-Host "Found ACR: $acr"

# Assign AcrPush role
Write-Host "Assigning AcrPush role to Service Principal..."
$assign = az role assignment create --assignee $clientId --role "AcrPush" --scope $acr 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: Failed to assign AcrPush role. You may already have permission or need Owner rights." -ForegroundColor Yellow
    Write-Host $assign
} else {
    Write-Host "AcrPush role successfully assigned to $clientId" -ForegroundColor Green
}

Write-Host ""
Write-Host "Validation complete. You can now re-run your GitHub Action build_push stage." -ForegroundColor Green
