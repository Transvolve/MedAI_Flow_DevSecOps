# LDRA Integration in CI/CD Workflow

**Date:** November 19, 2025  
**Status:** Phase 3 Ready (Deferred - License Required)  
**Purpose:** Show how to integrate LDRA Test Master into GitHub Actions workflow

---

## Current State: Plugin Architecture Ready

### Architecture Overview

```
┌─────────────────────────────────────┐
│   Application Code (No LDRA)        │
│   - FastAPI routes                  │
│   - Business logic                  │
│   - Test suites                     │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│   Analysis Factory Pattern          │
│   - create_analyzer(type)           │
│   - Auto-detect available tools     │
│   - Seamless plugin swapping        │
└──────────────┬──────────────────────┘
               │
        ┌──────┴──────────┬──────────┐
        ↓                 ↓          ↓
   ┌─────────┐      ┌─────────┐  ┌────────┐
   │ Local   │      │  LDRA   │  │  Mock  │
   │Analyzer │      │Adapter  │  │Analyzer│
   │(Always) │      │(Licensed)  │(Tests) │
   └─────────┘      └─────────┘  └────────┘
```

### Current Implementation

**Without LDRA License:**
```python
from backend.app.analysis import create_analyzer

# Automatically uses LocalAnalyzer
analyzer = create_analyzer("local")
result = analyzer.analyze_file("backend/app/main.py")

# Tools: flake8, bandit, pytest-cov, AST analysis
```

**With LDRA License (Future):**
```python
from backend.app.analysis import create_analyzer

# Automatically uses LDRAAdapter
analyzer = create_analyzer("ldra")
result = analyzer.analyze_file("backend/app/main.py")

# Tools: LDRA Test Master analysis
```

---

## Phase 3: LDRA Integration Steps

### Step 1: Obtain LDRA License

**Cost:** $3,000-5,000/year  
**Contact:** LDRA/Helix QAC sales team  
**Requirements:**
- Company information
- Project specifications
- Deployment environment (single user, team, cloud)

### Step 2: Install LDRA SDK

**Option A: Via pip (when available)**
```bash
pip install ldra-sdk
# OR for specific version
pip install ldra-sdk==2024.1.0
```

**Option B: Manual Installation**
1. Download LDRA SDK from vendor
2. Extract to `C:\Program Files\LDRA` (Windows) or `/opt/ldra` (Linux)
3. Configure environment variable:
   ```
   LDRA_HOME=C:\Program Files\LDRA
   PATH=%LDRA_HOME%\bin;%PATH%
   ```

### Step 3: Configure LDRA Project

```bash
# Create LDRA project for MedAI_Flow
ldra_config_tool create-project \
  --name "MedAI_Flow" \
  --path "C:\Users\mpanc\Documents\GitHub\MedAI_Flow_DevSecOps" \
  --analysis-level comprehensive

# Initialize LDRA project
ldra_builder init
```

### Step 4: Update Requirements

**Add to `requirements-security.txt`:**
```
# LDRA Test Master SDK (when licensed)
ldra-sdk>=2024.0.0
```

### Step 5: Update CI/CD Workflow

**Add to `.github/workflows/main.yml` - New Stage (between Stage 2 and 3):**

```yaml
  # ---------------------------
  # LDRA Analysis (Phase 3)
  # ---------------------------
  ldra_analysis:
    runs-on: ubuntu-latest
    needs: test
    if: env.LDRA_LICENSE != '' && github.event_name != 'pull_request'
    
    env:
      LDRA_LICENSE: ${{ secrets.LDRA_LICENSE }}
      LDRA_PROJECT_PATH: /opt/ldra/projects/MedAI_Flow
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install LDRA SDK
        run: |
          pip install ldra-sdk
          ldra_config_tool verify-installation

      - name: Run LDRA Analysis
        run: |
          python -m backend.analysis_cli analyze-file backend/app/main.py --analyzer ldra

      - name: Generate LDRA Report
        run: |
          python -m backend.analysis_cli report backend/app --analyzer ldra --format json

      - name: Upload LDRA Report
        uses: actions/upload-artifact@v4
        with:
          name: ldra-analysis-report
          path: ldra-report.json

      - name: Comment PR with LDRA Results
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const report = JSON.parse(fs.readFileSync('ldra-report.json', 'utf8'));
            const comment = `## LDRA Analysis Results
            - **Violations Found:** ${report.violation_count}
            - **Critical:** ${report.critical_count}
            - **High:** ${report.high_count}
            - **Medium:** ${report.medium_count}
            `;
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: comment
            });
```

---

## Using LDRA in Current Workflow

### Before License Arrives

**Status:** LocalAnalyzer active (full functionality available)

```bash
# All commands work with LocalAnalyzer
python -m backend.analysis_cli analyze-file backend/app/main.py
python -m backend.analysis_cli analyze-dir backend/app
python -m backend.analysis_cli metrics backend/app/main.py
python -m backend.analysis_cli report backend/app
```

### After License Arrives

**Status:** LDRAAdapter can be used (drop-in replacement)

```bash
# Use LDRA directly
python -m backend.analysis_cli analyze-file backend/app/main.py --analyzer ldra

# Or configure default in environment
export ANALYSIS_TOOL=ldra
python -m backend.analysis_cli analyze-file backend/app/main.py
```

---

## Local LDRA Testing (When Licensed)

### Test 1: Verify LDRA Installation

```powershell
# PowerShell
python -m backend.analysis_cli status

# Expected output:
# [OK] Analysis system is operational
# Available analyzers:
#   - local (flake8, bandit, AST, pytest-cov) - AVAILABLE
#   - ldra (LDRA Test Master) - AVAILABLE
#   - mock (Mock analyzer) - AVAILABLE
```

### Test 2: Analyze with LDRA

```powershell
# Analyze single file
python -m backend.analysis_cli analyze-file backend/app/main.py --analyzer ldra

# Expected output:
# [OK] Analysis complete
# File: backend/app/main.py
# Tool: LDRA Test Master
# Violations: {count}
# Time: {duration}ms
```

### Test 3: Compare Local vs LDRA

```powershell
# Run both analyzers and compare
python -m backend.analysis_cli analyze-file backend/app/main.py --analyzer local
python -m backend.analysis_cli analyze-file backend/app/main.py --analyzer ldra

# Typical comparison:
# LocalAnalyzer: 15 violations (style, security, complexity)
# LDRAAdapter: 25 violations (adds traceability, compliance checks)
```

### Test 4: Generate LDRA Report

```powershell
# Generate compliance report with LDRA
python -m backend.analysis_cli report backend/app --analyzer ldra --format json

# Output: ldra-analysis-report.json with:
# - Violations per severity
# - Traceability mapping
# - Test coverage analysis
# - Compliance matrix
```

---

## GitHub Secrets for LDRA

### Add to GitHub Repository Settings

**Settings > Secrets and variables > Actions**

| Secret | Value | Example |
|--------|-------|---------|
| `LDRA_LICENSE` | LDRA license key | `LDRA-XXXX-XXXX-XXXX-XXXX` |
| `LDRA_PROJECT_PATH` | Project configuration path | `/opt/ldra/projects/MedAI_Flow` |

---

## Workflow Integration Strategy

### Option 1: Always Active (Post-License)

```yaml
ldra_analysis:
  needs: test
  # No condition - runs on all branches
```

### Option 2: Main Branch Only

```yaml
ldra_analysis:
  needs: test
  if: github.ref == 'refs/heads/main'
```

### Option 3: Conditional on License

```yaml
ldra_analysis:
  needs: test
  if: env.LDRA_LICENSE != ''
```

### Option 4: Manual Trigger

```yaml
ldra_analysis:
  needs: test
  if: github.event.inputs.run_ldra == 'true'
```

---

## LDRA Features for Medical Device

### Traceability Mapping

```python
# LDRA provides bidirectional traceability:
# Requirements → Code → Tests → Coverage

traceability = analyzer.get_traceability()
# Output:
# {
#   "requirement_id": "REQ-001",
#   "code_files": ["backend/app/validation.py"],
#   "test_files": ["tests/test_validation.py"],
#   "coverage": 98.5%
# }
```

### Compliance Analysis

```python
# LDRA generates compliance matrices for:
# - FDA 21 CFR 11
# - ISO 13485
# - IEC 62304
# - DO-178C

compliance = analyzer.get_compliance_matrix()
# Output:
# {
#   "framework": "IEC 62304",
#   "controls": [
#     {"id": "5.3.1", "status": "compliant", "evidence": [...]}
#   ]
# }
```

### Test Generation

```python
# LDRA can automatically generate tests:
# - Unit tests for uncovered code
# - Integration tests
# - Coverage-driven tests

generated_tests = analyzer.generate_tests()
# Output: Test files in tests/generated/
```

---

## Recommended Implementation Order

### Phase 3 Roadmap

```
Week 1-2: LDRA License & Setup
  ✓ Obtain LDRA license
  ✓ Install LDRA SDK
  ✓ Configure LDRA project

Week 3: Integration Testing
  ✓ Test LDRA adapter locally
  ✓ Verify analyzer factory pattern
  ✓ Compare Local vs LDRA output

Week 4: CI/CD Integration
  ✓ Add LDRA stage to workflow
  ✓ Configure GitHub secrets
  ✓ Test workflow with LDRA

Week 5: Compliance Generation
  ✓ Generate FDA compliance matrix
  ✓ Generate ISO compliance matrix
  ✓ Document compliance gaps
```

---

## Expected Workflow Times

| Analyzer | Time | Coverage |
|----------|------|----------|
| Local (flake8, bandit) | 2-3 min | Basic |
| Local + pytest | 3-5 min | Comprehensive |
| LDRA (analysis only) | 5-10 min | Industrial |
| LDRA (with test gen) | 10-20 min | Complete |
| Full Pipeline | 20-35 min | Full stack |

---

## Troubleshooting LDRA

### Issue: LDRA SDK not found
```
Error: ldra-sdk is not installed
Solution: pip install ldra-sdk
```

### Issue: LDRA License invalid
```
Error: LDRA_LICENSE environment variable not set
Solution: Configure GitHub secret LDRA_LICENSE
```

### Issue: LDRA Project not configured
```
Error: No LDRA project found at path
Solution: Run ldra_builder init in project directory
```

### Issue: LDRA analysis timeout
```
Error: LDRA analysis exceeded time limit
Solution: Reduce analysis scope or increase timeout
```

---

## Next Steps (After License)

1. **Install LDRA SDK**
   ```bash
   pip install ldra-sdk
   ```

2. **Update requirements files**
   ```
   Add ldra-sdk to requirements-security.txt
   ```

3. **Test locally**
   ```bash
   python -m backend.analysis_cli analyze-file backend/app/main.py --analyzer ldra
   ```

4. **Configure GitHub secrets**
   - LDRA_LICENSE
   - LDRA_PROJECT_PATH

5. **Update workflow YAML**
   - Add LDRA analysis stage
   - Configure conditions
   - Add artifact uploads

6. **Test CI/CD**
   - Push to main branch
   - Verify LDRA stage executes
   - Review LDRA report

---

## Resources

- [LDRA Documentation](https://www.ldra.com/documentation/)
- [LDRA SDK GitHub](https://github.com/ldra/ldra-sdk)
- [Medical Device Compliance Guide](docs/reference/COMPLETE_DEVELOPMENT_PLAN.md)
- [LDRA Integration Guide](docs/reference/README_LDRA_IMPLEMENTATION.md)

---

**Document Version:** 1.0  
**Status:** Phase 3 Planning  
**Next Review:** After LDRA License Acquisition
