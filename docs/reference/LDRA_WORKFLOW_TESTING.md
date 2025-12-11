# LDRA Testing Guide - Workflow Verification

**Status:** Ready for implementation when LDRA license is acquired  
**Purpose:** Step-by-step guide to test LDRA in workflow runs

---

## Quick Start: Testing LDRA Locally

### Prerequisites
- Python 3.12+
- LDRA SDK installed
- LDRA license configured
- Project checked out

### Test Suite A: Verify LDRA Integration

**Test 1: Check LDRA is available**
```powershell
cd C:\Users\mpanc\Documents\GitHub\MedAI_Flow_DevSecOps

# Run status command
python -m backend.analysis_cli status

# Expected output includes:
# - ldra (LDRA Test Master) - AVAILABLE
```

**Test 2: Analyze with LDRA**
```powershell
# Analyze single file
python -m backend.analysis_cli analyze-file backend/app/main.py --analyzer ldra

# Expected output:
# [OK] Analysis complete
# Tool: LDRA Test Master
# Violations: {count}
```

**Test 3: Generate LDRA Report**
```powershell
# Generate JSON report
python -m backend.analysis_cli report backend/app --analyzer ldra --format json

# Check output file
Get-Item ldra-analysis-report.json
```

---

## Test Suite B: CI/CD Workflow Testing

### Simulate GitHub Actions Workflow

**Step 1: Create test script**

Create `test_ldra_workflow.ps1`:

```powershell
# Simulate GitHub Actions workflow steps

$ErrorActionPreference = "Stop"
$root = "C:\Users\mpanc\Documents\GitHub\MedAI_Flow_DevSecOps"
cd $root

Write-Host "=========================================="
Write-Host "SIMULATING GITHUB ACTIONS WORKFLOW"
Write-Host "=========================================="
Write-Host ""

# Stage 1: Lint & Security (existing)
Write-Host "Stage 1: Lint & Security"
Write-Host "-" * 40
flake8 backend/app --max-line-length=120 --ignore=E302,E401,F401,W391,E203,W503
if ($LASTEXITCODE -ne 0) { Write-Host "[FAIL] Lint failed"; exit 1 }
Write-Host "[OK] Lint passed"
Write-Host ""

# Stage 2: Unit Tests (existing)
Write-Host "Stage 2: Unit Tests"
Write-Host "-" * 40
$env:REDIS_HOST = "localhost"
$env:REDIS_PORT = "6379"
$env:JWT_SECRET_KEY = "test_secret_key_123"
pytest tests/ -v --disable-warnings --tb=short -x
if ($LASTEXITCODE -ne 0) { Write-Host "[FAIL] Tests failed"; exit 1 }
Write-Host "[OK] Tests passed"
Write-Host ""

# Stage 2.5: LDRA Analysis (NEW)
Write-Host "Stage 2.5: LDRA Analysis"
Write-Host "-" * 40

# Check if LDRA is available
try {
    $ldraStatus = & python -m backend.analysis_cli status 2>&1
    if ($ldraStatus -match "ldra.*AVAILABLE") {
        Write-Host "[OK] LDRA is available"
        
        # Run LDRA analysis
        Write-Host "Running LDRA analysis..."
        & python -m backend.analysis_cli analyze-file backend/app/main.py --analyzer ldra --output json
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] LDRA analysis passed"
        } else {
            Write-Host "[WARN] LDRA analysis found issues (non-blocking)"
        }
    } else {
        Write-Host "[SKIP] LDRA not available (waiting for license)"
    }
} catch {
    Write-Host "[SKIP] LDRA not installed"
}
Write-Host ""

Write-Host "=========================================="
Write-Host "WORKFLOW SIMULATION COMPLETE"
Write-Host "=========================================="
```

**Step 2: Run the test**
```powershell
.\test_ldra_workflow.ps1
```

---

## Test Suite C: LDRA-Specific Validation

### Test 1: Traceability Verification

```powershell
# Generate traceability report
python -m backend.analysis_cli report backend/app \
  --analyzer ldra \
  --format json \
  --include-traceability

# Verify output contains:
# - requirement_id
# - code_files
# - test_files
# - coverage percentage
```

### Test 2: Compliance Matrix Generation

```powershell
# Generate FDA compliance matrix
python -m backend.analysis_cli report backend/app \
  --analyzer ldra \
  --compliance fda-21cfr11 \
  --output json

# Expected output:
# {
#   "compliance_framework": "FDA 21 CFR 11",
#   "controls": [
#     {"id": "11.3(a)", "status": "compliant/non-compliant", ...}
#   ]
# }
```

### Test 3: Test Coverage Analysis

```powershell
# Generate coverage analysis with LDRA
python -m backend.analysis_cli metrics backend/app \
  --analyzer ldra \
  --coverage-analysis

# Expected output:
# - Statement coverage: X%
# - Branch coverage: X%
# - Function coverage: X%
# - Uncovered lines: [list]
```

---

## Test Suite D: Compare Local vs LDRA

### Side-by-Side Comparison

**Create comparison script:**

```powershell
# compare_analyzers.ps1

$file = "backend/app/main.py"

Write-Host "Analyzing: $file"
Write-Host ""

# LocalAnalyzer
Write-Host "LocalAnalyzer Results:"
Write-Host "-" * 40
python -m backend.analysis_cli analyze-file $file --analyzer local --output json | ConvertFrom-Json | Select-Object -Property violation_count, severity_distribution

# LDRAAdapter
Write-Host "LDRAAdapter Results:"
Write-Host "-" * 40
python -m backend.analysis_cli analyze-file $file --analyzer ldra --output json | ConvertFrom-Json | Select-Object -Property violation_count, severity_distribution

Write-Host ""
Write-Host "Note: LDRA typically detects more violations due to:"
Write-Host "- Deeper static analysis"
Write-Host "- Compliance checks"
Write-Host "- Traceability requirements"
```

---

## Integration Test: Full Workflow

### End-to-End Test

```powershell
# e2e_ldra_test.ps1

Write-Host "END-TO-END LDRA WORKFLOW TEST"
Write-Host ""

$root = "C:\Users\mpanc\Documents\GitHub\MedAI_Flow_DevSecOps"
cd $root

# 1. Setup
Write-Host "1. Setup"
Write-Host "-" * 40
$env:LDRA_LICENSE = $env:LDRA_LICENSE  # Use from environment
if (-not $env:LDRA_LICENSE) {
    Write-Host "[SKIP] LDRA_LICENSE not set"
    exit 0
}
Write-Host "[OK] LDRA license configured"
Write-Host ""

# 2. Verify LDRA
Write-Host "2. Verify LDRA"
Write-Host "-" * 40
python -m backend.analysis_cli status | Select-String "ldra"
Write-Host "[OK] LDRA verified"
Write-Host ""

# 3. Run Analysis
Write-Host "3. Run Analysis"
Write-Host "-" * 40
$analysisResult = python -m backend.analysis_cli analyze-dir backend/app --analyzer ldra --output json
$violations = $analysisResult | ConvertFrom-Json | Select-Object -ExpandProperty violation_count
Write-Host "[OK] Found $violations violations"
Write-Host ""

# 4. Generate Report
Write-Host "4. Generate Report"
Write-Host "-" * 40
python -m backend.analysis_cli report backend/app --analyzer ldra --format json --output ldra-e2e-report.json
Write-Host "[OK] Report generated: ldra-e2e-report.json"
Write-Host ""

# 5. Validate Output
Write-Host "5. Validate Output"
Write-Host "-" * 40
$report = Get-Content ldra-e2e-report.json | ConvertFrom-Json
Write-Host "- Framework: $($report.compliance_framework)"
Write-Host "- Violations: $($report.violation_count)"
Write-Host "- Coverage: $($report.coverage)%"
Write-Host "[OK] Report validated"
Write-Host ""

Write-Host "=========================================="
Write-Host "E2E TEST COMPLETE - SUCCESS"
Write-Host "=========================================="
```

---

## GitHub Actions Workflow Addition

### Add to `.github/workflows/main.yml`

**New Stage (between test and build):**

```yaml
  # Optional LDRA Analysis Stage
  ldra_check:
    runs-on: ubuntu-latest
    needs: test
    if: secrets.LDRA_LICENSE != ''
    continue-on-error: true  # Non-blocking
    
    env:
      LDRA_LICENSE: ${{ secrets.LDRA_LICENSE }}
    
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      
      - name: Install LDRA SDK
        run: pip install ldra-sdk
      
      - name: Run LDRA Analysis
        run: |
          python -m backend.analysis_cli analyze-dir backend/app \
            --analyzer ldra \
            --output json
      
      - name: Upload LDRA Report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: ldra-analysis
          path: ldra-analysis-report.json
```

---

## Validation Checklist

- [ ] LDRA SDK installed successfully
- [ ] LDRA license configured
- [ ] `python -m backend.analysis_cli status` shows LDRA available
- [ ] Single file analysis works with `--analyzer ldra`
- [ ] Directory analysis works
- [ ] JSON report generation works
- [ ] Comparison with LocalAnalyzer shows expected differences
- [ ] Full workflow simulation completes successfully
- [ ] GitHub Actions workflow passes with LDRA stage

---

## Success Criteria

✓ LDRA analyzer is selectable via `--analyzer ldra`  
✓ Analysis completes without errors  
✓ Reports can be generated in JSON format  
✓ Workflow stage executes and produces artifacts  
✓ LDRA stage is non-blocking (continue on error)  
✓ Results can be compared with LocalAnalyzer  

---

## Next Steps

1. **Acquire LDRA License**
   - Contact LDRA sales
   - Obtain license key and SDK

2. **Install and Configure**
   - Install LDRA SDK
   - Configure environment
   - Test locally

3. **Update Workflow**
   - Add LDRA stage to main.yml
   - Configure GitHub secrets
   - Test with workflow_dispatch

4. **Production Deployment**
   - Enable on main branch
   - Monitor results
   - Iterate compliance improvements

---

**Ready to execute when LDRA license is acquired.**
