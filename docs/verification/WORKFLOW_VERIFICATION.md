# CI/CD Workflow Verification Guide

**Date:** November 19, 2025  
**Status:** Ready for Production  
**Stages:** 4 CI/CD Pipeline Stages

---

## Workflow Overview

The MedAI Flow DevSecOps project uses a 4-stage CI/CD pipeline implemented in `.github/workflows/main.yml`:

| Stage | Name | Trigger | Requirements | Status |
|-------|------|---------|--------------|--------|
| 1 | Lint & Security | Push/PR | Python 3.12, flake8, bandit, safety | [OK] Testable Locally |
| 2 | Unit Testing | After Stage 1 | pytest, Redis | [OK] Testable Locally |
| 3 | Build & Push | Main branch only | Azure ACR, Docker | [READY] Prod Only |
| 4 | Deploy to AKS | Main/workflow_dispatch | Azure AKS, kubectl | [READY] Prod Only |

---

## Stage 1: Lint & Security Scan

### Purpose
Ensure code quality and security compliance before testing.

### Tools & Tasks
```
✓ Flake8           - Code style & linting (PEP 8)
✓ Bandit           - Security vulnerability scanning
✓ Safety           - Python package vulnerability check
```

### Commands (Test Locally)

**Flake8 Linting:**
```bash
flake8 backend/app --max-line-length=120 \
  --ignore=E302,E401,F401,W391,E203,W503 \
  --statistics
```

**Expected Output:**
```
0 (No errors)
```

**Bandit Security Scan:**
```bash
bandit -r backend/app -ll --skip B101,B104 \
  --exclude backend/app/tests
```

**Expected Output:**
```
[OK] No issues identified
```

**Safety Dependency Check:**
```bash
safety check -r requirements-ci.txt \
  --ignore=51457 \
  --full-report
```

### Local Verification
```powershell
cd C:\Users\mpanc\Documents\GitHub\MedAI_Flow_DevSecOps
flake8 backend/app --max-line-length=120 --ignore=E302,E401,F401,W391,E203,W503 --statistics
bandit -r backend/app -ll --skip B101,B104 --exclude backend/app/tests
```

**Status:** ✓ [OK] - No errors expected

---

## Stage 2: Unit Testing

### Purpose
Verify all code functionality with comprehensive test coverage.

### Requirements
- Python 3.12
- pytest with plugins
- Redis service (localhost:6379)
- Test environment variables

### Commands (Test Locally)

**Run All Tests:**
```bash
pytest tests/ -v --disable-warnings --cov=backend/app --cov-report=term-missing
```

**Run Specific Test Suite:**
```bash
pytest tests/unit/test_validation.py -v
pytest tests/unit/test_analysis_api.py -v
```

**With Environment Variables:**
```powershell
$env:REDIS_HOST = "localhost"
$env:REDIS_PORT = "6379"
$env:JWT_SECRET_KEY = "test_secret_key_123"
$env:ALGORITHM = "HS256"
$env:ACCESS_TOKEN_EXPIRE_MINUTES = "30"
$env:ENVIRONMENT = "ci"
$env:PYTHONWARNINGS = "ignore::UserWarning,ignore:PydanticDeprecatedSince20"

pytest tests/ -v --disable-warnings --cov=backend/app --cov-report=term-missing
```

### Test Coverage

**Test Statistics:**
```
Phase 2.1: Input Validation           43 tests [OK]
Phase 2.2: Logging & Audit            54 tests [OK]
Phase 2.3: Error Handling             51 tests [OK]
Phase 2.4: Configuration              45 tests [OK]
Phase 2.5: Health Monitoring          33 tests [OK]
Phase 2.6: Database Integration       33 tests [OK]
Phase 2.7: API Enhancements           51 tests [OK]
─────────────────────────────────────────────────
Total:                               310 tests
Expected Pass Rate:                   100%
```

### Prerequisites for Testing

**Redis Service:**
```powershell
# Option 1: Docker (recommended)
docker run -d -p 6379:6379 redis:latest

# Option 2: Windows Subsystem for Linux
redis-server --port 6379

# Option 3: Local Redis installation
redis-server
```

**Verify Redis Connection:**
```powershell
redis-cli ping
# Expected output: PONG
```

### Local Verification
```powershell
cd C:\Users\mpanc\Documents\GitHub\MedAI_Flow_DevSecOps

# Ensure Redis is running
redis-cli ping

# Set environment variables
$env:REDIS_HOST = "localhost"
$env:REDIS_PORT = "6379"
$env:JWT_SECRET_KEY = "test_secret_key_123"

# Run tests
pytest tests/ -v --cov=backend/app
```

**Expected Output:**
```
========== 310 passed in X.XXs ==========
Coverage: XX%
```

**Status:** ✓ [OK] - 310 tests, 100% pass rate expected

---

## Stage 3: Build & Push Docker Image

### Purpose
Create production-ready Docker image and push to Azure Container Registry (ACR).

### Requirements
- Azure account with ACR
- `AZURE_CREDENTIALS` GitHub secret
- Docker buildx installed
- Dockerfile in `backend/Dockerfile`

### Process

1. **Azure Login**
   - Uses AZURE_CREDENTIALS secret
   - Authenticates with Azure service principal

2. **ACR Login**
   - Connects to Azure Container Registry
   - Prepares for image push

3. **Docker Build & Push**
   - Builds image from `backend/Dockerfile`
   - Tags with version: `v{run_number}-{sha}`
   - Tags with: `latest`
   - Pushes to ACR: `{ACR_NAME}.azurecr.io/medai_flow_backend`

### Conditions
- **Triggers:** Only on push to `main` branch
- **Skips:** Pull requests, feature branches
- **Manual:** Can trigger via `workflow_dispatch`

### Commands (Production Only)

```bash
# Build image
docker build -f backend/Dockerfile -t medai_flow_backend:latest .

# Tag for ACR
docker tag medai_flow_backend:latest \
  {ACR_NAME}.azurecr.io/medai_flow_backend:latest

# Push to ACR
docker push {ACR_NAME}.azurecr.io/medai_flow_backend:latest
```

### Environment Variables
```
ACR_NAME: From AZURE_CREDENTIALS secret
RESOURCE_GROUP: From GitHub secret
VERSION_TAG: v{github.run_number}-{github.sha}
LATEST_TAG: latest
```

### Verification (in GitHub Actions)
- Check: `Actions` tab in GitHub
- View: Build logs for tag names
- Verify: Image appears in Azure ACR portal

**Status:** ✓ [READY] - Configured and ready for production

---

## Stage 4: Deploy to AKS

### Purpose
Deploy built Docker image to Azure Kubernetes Service (AKS) cluster.

### Requirements
- AKS cluster provisioned
- `AZURE_CREDENTIALS` GitHub secret
- `AKS_CLUSTER` GitHub secret
- `RESOURCE_GROUP` GitHub secret
- kubectl configuration file
- Kubernetes manifests in `infra/aks_deploy.yaml`

### Process

1. **Azure Login**
   - Uses AZURE_CREDENTIALS secret
   - Authenticates with Azure service principal

2. **Get AKS Credentials**
   ```bash
   az aks get-credentials \
     --resource-group {RESOURCE_GROUP} \
     --name {AKS_CLUSTER} \
     --overwrite-existing
   ```

3. **Apply Kubernetes Manifests**
   ```bash
   kubectl apply -f infra/aks_deploy.yaml
   ```

4. **Verify Deployment**
   ```bash
   kubectl rollout status deployment/medai-flow-deployment
   kubectl get pods -o wide
   kubectl get services
   ```

### Conditions
- **Triggers:** 
  - Push to `main` branch
  - Manual `workflow_dispatch`
- **Skips:** Pull requests, feature branches

### Environment Variables
```
RESOURCE_GROUP: From GitHub secret
AKS_CLUSTER: From GitHub secret
```

### Verification (in GitHub Actions)
- Check: `Actions` tab deployment logs
- View: Pod status in AKS cluster
- Verify: Service endpoints are accessible

**Status:** ✓ [READY] - Configured and ready for production

---

## Local Testing Checklist

Before pushing to GitHub, verify locally:

### Checklist

- [ ] **Stage 1: Lint**
  ```powershell
  flake8 backend/app --max-line-length=120 --ignore=E302,E401,F401,W391,E203,W503
  ```
  Expected: No errors

- [ ] **Stage 1: Security**
  ```powershell
  bandit -r backend/app -ll --skip B101,B104 --exclude backend/app/tests
  ```
  Expected: No high-risk issues

- [ ] **Stage 2: Dependencies**
  ```powershell
  safety check -r requirements-ci.txt --ignore=51457
  ```
  Expected: No vulnerabilities

- [ ] **Stage 2: Tests**
  ```powershell
  $env:REDIS_HOST = "localhost"
  $env:REDIS_PORT = "6379"
  pytest tests/ -v --cov=backend/app
  ```
  Expected: 310 tests passed

- [ ] **Docker Build** (optional)
  ```bash
  docker build -f backend/Dockerfile -t medai_flow_backend:test .
  ```
  Expected: Build succeeds

---

## GitHub Secrets Required

For stages 3 & 4 to work, configure these GitHub secrets:

### Settings > Secrets and variables > Actions

| Secret Name | Value | Example |
|-------------|-------|---------|
| `AZURE_CREDENTIALS` | JSON service principal | `{"clientId":"...","clientSecret":"..."}` |
| `ACR_NAME` | Azure Container Registry name | `medaiflowacr` |
| `AKS_CLUSTER` | AKS cluster name | `medai-flow-aks` |
| `RESOURCE_GROUP` | Azure resource group | `medai-flow-rg` |

---

## Troubleshooting

### Stage 1: Flake8 Errors
**Problem:** Linting fails with PEP 8 violations  
**Solution:** Fix issues or update `.flake8` configuration

### Stage 2: Test Failures
**Problem:** pytest fails with "redis connection refused"  
**Solution:** Ensure Redis is running on localhost:6379

### Stage 3: Build Fails
**Problem:** Docker build fails  
**Solution:** Check `backend/Dockerfile` exists and is valid

### Stage 4: Deployment Fails
**Problem:** kubectl apply fails  
**Solution:** Verify Azure credentials and AKS cluster access

---

## Timeline & Performance

| Stage | Approx. Time | Optimization |
|-------|-------------|--------------|
| Stage 1 | 2-3 min | Cached pip packages |
| Stage 2 | 3-5 min | Cached Redis service |
| Stage 3 | 5-10 min | Docker layer caching |
| Stage 4 | 2-3 min | kubectl direct apply |
| **Total** | **12-21 min** | **- Full pipeline** |

---

## Success Criteria

✓ All 4 stages pass  
✓ No security vulnerabilities  
✓ 310+ tests passing (100% pass rate)  
✓ Docker image pushed to ACR  
✓ Pod running in AKS cluster  

---

## Next Steps

1. **Local Testing**
   - Run stages 1-2 locally before pushing
   - Use provided commands above

2. **GitHub Push**
   - Push to feature branch for PR (tests stages 1-2)
   - Push to main for full pipeline (all 4 stages)

3. **Monitor Workflow**
   - Check `Actions` tab in GitHub
   - Review logs if any stage fails

4. **Production Deployment**
   - Verify AKS cluster is healthy
   - Check deployed pods and services

---

**Document Version:** 1.0  
**Last Updated:** November 19, 2025  
**Status:** Production Ready
