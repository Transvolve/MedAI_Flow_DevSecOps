# Development Plan: Regulatory-Compliant Medical AI Platform

**Target:** Production-ready, regulatory-compliant medical AI platform suitable for FDA submissions and commercial contracts.

**Timeline:** 6-8 weeks for MVP, then iterative improvements

---

## ✅ Completed (Already Built)

- ✅ Typed POST `/infer` API with Pydantic request/response models
- ✅ Environment-based configuration (Pydantic BaseSettings)
- ✅ Request middleware with correlation IDs and timing
- ✅ ONNX session caching for performance
- ✅ CI/CD pipeline with lint, security, test, build, deploy stages
- ✅ Basic security (Bearer token authentication)
- ✅ Type hints across core modules

---

## 🎯 Phase 1: Security Hardening (Week 1-2)
**Priority: HIGH** — Required for regulatory compliance and commercial contracts

### 1.1 JWT-Based Authentication
- Replace simple token with JWT (expiration, audience, issuer validation)
- Add role-based access control (RBAC): `admin`, `clinician`, `service`
- Token rotation mechanism
- Secure token storage (Azure Key Vault integration)

**Deliverables:**
- `backend/app/auth/jwt.py` — JWT encoding/decoding with exp/aud/iss validation
- `backend/app/auth/roles.py` — Role-based permission decorators
- Updated `security.py` to use JWT instead of simple token
- Environment variables for JWT secret and rotation keys

**Files to Create/Modify:**
- `backend/app/auth/__init__.py`
- `backend/app/auth/jwt.py`
- `backend/app/auth/roles.py`
- `backend/app/security.py` (update)
- `backend/app/config.py` (add JWT settings)

### 1.2 Security Headers Middleware
- Add security headers: HSTS, X-Content-Type-Options, CSP, X-Frame-Options
- Rate limiting (prevent abuse)
- CORS configuration for production

**Deliverables:**
- `backend/app/middleware/security.py` — Security headers middleware
- `backend/app/middleware/rate_limit.py` — Rate limiting (using slowapi or similar)
- Updated `main.py` to register middleware

**Files to Create/Modify:**
- `backend/app/middleware/security.py`
- `backend/app/middleware/rate_limit.py`
- `backend/app/main.py` (update)

### 1.3 Dependency Updates
- Add `python-jose[cryptography]` for JWT
- Add `slowapi` for rate limiting
- Update `requirements-ci.txt`

---

## 🎯 Phase 2: Input Validation & Error Handling (Week 2-3)
**Priority: HIGH** — Critical for regulatory compliance (IEC 62304, ISO 14971)

### 2.1 Enhanced Input Validation
- Validate image dimensions, dtype, normalization bounds
- Clinical constraints (e.g., pixel value ranges, image size limits)
- Clear error messages for validation failures

**Deliverables:**
- `backend/app/validation/image_validator.py` — Image validation utilities
- Updated `InferenceRequest` model with stricter validation
- Shape validation for ONNX model inputs (discover from session metadata)

**Files to Create/Modify:**
- `backend/app/validation/__init__.py`
- `backend/app/validation/image_validator.py`
- `backend/app/routes.py` (update InferenceRequest)
- `ml/inference.py` (add input shape validation)

### 2.2 Centralized Error Handling
- Custom exception classes for different error types
- Consistent error response format
- Safe error messages (no PHI leakage)
- Error logging with correlation IDs

**Deliverables:**
- `backend/app/exceptions.py` — Custom exception classes
- `backend/app/error_handlers.py` — FastAPI exception handlers
- Updated `main.py` to register error handlers

**Files to Create/Modify:**
- `backend/app/exceptions.py`
- `backend/app/error_handlers.py`
- `backend/app/main.py` (update)

---

## 🎯 Phase 3: Structured Logging & Audit Trails (Week 3-4)
**Priority: HIGH** — Required for ISO 27001, HIPAA, FDA traceability

### 3.1 Structured Logging
- Replace basic logging with structured JSON logging
- Correlation IDs for request tracing
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- PHI-safe logging (no sensitive data in logs)

**Deliverables:**
- `backend/app/logging/__init__.py`
- `backend/app/logging/structured.py` — JSON structured logger
- `backend/app/logging/filters.py` — PHI filtering
- Updated middleware to inject correlation IDs

**Files to Create/Modify:**
- `backend/app/logging/__init__.py`
- `backend/app/logging/structured.py`
- `backend/app/logging/filters.py`
- `backend/app/middleware.py` (update)
- `backend/app/main.py` (update)

### 3.2 Audit Trail
- Tamper-evident audit log (append-only, hash chain)
- Log key events: authentication, inference requests, errors
- Export audit logs for compliance reviews

**Deliverables:**
- `backend/app/audit/__init__.py`
- `backend/app/audit/audit_log.py` — Audit logging service
- `backend/app/audit/export.py` — Export utilities

**Files to Create/Modify:**
- `backend/app/audit/__init__.py`
- `backend/app/audit/audit_log.py`
- `backend/app/audit/export.py`

### 3.3 Dependency Updates
- Add `python-json-logger` or `structlog`
- Update `requirements-ci.txt`

---

## 🎯 Phase 4: Test Coverage Expansion (Week 4-5)
**Priority: HIGH** — Required for regulatory validation (IEC 62304, FDA)

### 4.1 Unit Tests
- Test all modules: `config.py`, `security.py`, `routes.py`, `utils.py`, `ml/inference.py`
- Mock ONNX sessions for ML tests
- Test error handling paths

**Deliverables:**
- `tests/unit/test_config.py`
- `tests/unit/test_security.py`
- `tests/unit/test_routes.py`
- `tests/unit/test_ml_inference.py`
- `tests/unit/test_validation.py`

**Files to Create/Modify:**
- Create `tests/unit/` directory structure
- Add unit tests for each module

### 4.2 Integration Tests
- End-to-end API tests with TestClient
- Test authentication flows
- Test error scenarios
- Test rate limiting

**Deliverables:**
- `tests/integration/test_api_auth.py`
- `tests/integration/test_api_inference.py`
- `tests/integration/test_error_handling.py`

**Files to Create/Modify:**
- Create `tests/integration/` directory
- Expand `tests/test_api_endpoints.py`

### 4.3 Security Tests
- Test authentication bypass attempts
- Test input validation edge cases
- Test rate limiting enforcement

**Deliverables:**
- `tests/security/test_auth_bypass.py`
- `tests/security/test_input_validation.py`
- `tests/security/test_rate_limiting.py`

**Files to Create/Modify:**
- Create `tests/security/` directory
- Expand `tests/test_security.py`

### 4.4 Test Coverage Target
- Aim for >80% code coverage
- Add `pytest-cov` to requirements
- Generate coverage reports in CI

**Deliverables:**
- `.github/workflows/main.yml` — Add coverage reporting
- `pytest.ini` or `pyproject.toml` — Coverage configuration

---

## 🎯 Phase 5: CI/CD Enhancements (Week 5-6)
**Priority: MEDIUM-HIGH** — Improves quality gates and regulatory readiness

### 5.1 Static Type Checking
- Add `mypy` for type checking
- Configure mypy with strict mode
- Fix type errors across codebase

**Deliverables:**
- `mypy.ini` — Mypy configuration
- `.github/workflows/main.yml` — Add mypy step
- Update `requirements-ci.txt` (add `mypy`)

### 5.2 SBOM Generation
- Generate Software Bill of Materials (CycloneDX format)
- Include in CI/CD artifacts
- Required for FDA cybersecurity submissions

**Deliverables:**
- `.github/workflows/main.yml` — Add `cyclonedx-py` or `cyclonedx-bom` step
- Generate `sbom.json` or `sbom.xml` in CI artifacts

### 5.3 Vulnerability Scanning
- Add `pip-audit` to scan dependencies
- Add `trivy` or `snyk` for container scanning
- Fail CI if critical vulnerabilities found

**Deliverables:**
- `.github/workflows/main.yml` — Add vulnerability scanning steps
- Update `requirements-ci.txt` (add `pip-audit`)

### 5.4 Code Quality Tools
- Add `ruff` for fast linting (alternative to flake8)
- Add `black` for code formatting (optional but recommended)
- Add pre-commit hooks (optional)

**Deliverables:**
- `.github/workflows/main.yml` — Add ruff/black steps
- Update `requirements-ci.txt` (add `ruff`, `black`)

---

## 🎯 Phase 6: Documentation & Compliance Mapping (Week 6-7)
**Priority: MEDIUM** — Required for commercial contracts and regulatory submissions

### 6.1 README Updates
- Update README with compliance mapping
- Add deployment instructions
- Add buyer-facing executive summary
- Document security features

**Deliverables:**
- Updated `README.md` with:
  - Compliance mapping table (IEC 62304, ISO 13485, ISO 14971, ISO 27001, FDA 21 CFR 820)
  - Security features section
  - Deployment guide
  - API documentation link

### 6.2 API Documentation
- Enhance OpenAPI/Swagger docs with examples
- Add request/response schemas
- Document authentication flows

**Deliverables:**
- Enhanced FastAPI docs (automatic via OpenAPI)
- Manual API docs in `docs/api.md` (optional)

### 6.3 Compliance Documentation Updates
- Update traceability matrix with new code changes
- Link requirements → code → tests
- Update risk management file with new controls

**Deliverables:**
- Updated `compliance/TRACEABILITY_MATRIX.md`
- Updated `compliance/RISK_MANAGEMENT_FILE.md`

---

## 🎯 Phase 7: Commercial Readiness (Week 7-8)
**Priority: MEDIUM** — Enables immediate contracts and productization

### 7.1 Demo UI (Optional but Recommended)
- Simple Streamlit or React frontend
- Allow users to upload images and view inference results
- Professional UI with disclaimers

**Deliverables:**
- `frontend/` directory (Streamlit or React)
- Docker compose for local demo
- Hosted demo (optional)

### 7.2 Validation Reports
- Auto-generate validation reports from CI
- Include: test coverage, SBOM, vulnerability scan results, compliance checks
- Export as PDF or markdown

**Deliverables:**
- `.github/workflows/validation-report.yml` — Generate validation report
- `docs/validation-report.md` — Template

### 7.3 Pricing & Service Packages
- Define consultancy service packages:
  - **Quick Win:** 2-week regulatory hardening sprint ($15k-$30k)
  - **MLOps Kickstart:** 4-week MLOps and validation setup ($40k-$60k)
  - **Full Compliance:** 8-week end-to-end regulatory readiness ($80k-$120k)
- Retainer options for ongoing compliance

**Deliverables:**
- `docs/SERVICES.md` — Service packages document
- Update `README.md` with services section

---

## 📋 Implementation Priority Summary

| Phase | Priority | Timeline | Regulatory Impact | Commercial Impact |
|-------|----------|----------|-------------------|-------------------|
| Phase 1: Security | HIGH | Week 1-2 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Phase 2: Validation | HIGH | Week 2-3 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Phase 3: Logging | HIGH | Week 3-4 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Phase 4: Tests | HIGH | Week 4-5 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Phase 5: CI/CD | MEDIUM-HIGH | Week 5-6 | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Phase 6: Docs | MEDIUM | Week 6-7 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Phase 7: Commercial | MEDIUM | Week 7-8 | ⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 🚀 Quick Start: Immediate Next Steps (This Week)

1. **Start Phase 1.1: JWT Authentication**
   - Create `backend/app/auth/` directory
   - Implement JWT encoding/decoding
   - Update `security.py` to use JWT

2. **Start Phase 2.1: Input Validation**
   - Create `backend/app/validation/` directory
   - Add image validation utilities
   - Update `InferenceRequest` model

3. **Update README**
   - Add compliance mapping section
   - Add security features section
   - Update API documentation links

---

## 📝 Notes

- **Regulatory Standards:** Focus on IEC 62304 (software lifecycle), ISO 13485 (QMS), ISO 14971 (risk management), ISO 27001 (security), FDA 21 CFR 820 (quality system)
- **Commercial Strategy:** Position as "Regulatory-ready medical AI platform" for immediate contracts
- **Testing:** Maintain >80% coverage for regulatory validation
- **Documentation:** Keep traceability matrix updated with every code change

---

## 🎯 Success Metrics

- ✅ All 4 CI/CD stages pass consistently
- ✅ >80% test coverage
- ✅ Zero critical vulnerabilities in dependencies
- ✅ SBOM generated automatically
- ✅ JWT authentication with role-based access
- ✅ Structured logging with audit trails
- ✅ Comprehensive compliance documentation
- ✅ Professional demo UI (optional)
- ✅ Ready for FDA Q-Sub or commercial contracts

---

**Last Updated:** 2024-12-19
**Next Review:** After Phase 1 completion

