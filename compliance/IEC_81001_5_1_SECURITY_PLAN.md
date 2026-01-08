# IEC 81001-5-1 Security Development Plan

**Document ID**: SDP-81001-001  
**Version**: 1.0.0  
**Compliance Standard**: IEC 81001-5-1, Clause 5 (Software Development)  

---

## 1. Introduction

This plan documents the **Secure Software Development Lifecycle (Secure SDLC)** for MedAI Flow, in compliance with **IEC 81001-5-1 Health software and health IT systems safety, effectiveness and security**. It establishes the specific activities, tools, and responsibilities required to ensure the software is secure by design.

---

## 2. Development Activities & Security Gates

### 2.1. Requirements Phase (Clause 5.2)
*   **Activity**: Security Requirements Elicitation.
*   **Input**: Regulatory Strategy, User Needs.
*   **Output**: Security Requirements Specification.
*   **Control**: All requirements must include specific security acceptance criteria (e.g., "Authentication must use MFA").

### 2.2. Architecture Phase (Clause 5.3)
*   **Activity**: Secure Architecture Design & Threat Modeling.
*   **Methodology**: STRIDE (Spoofing, Tampering, Repudiation, Info Disclosure, Denial of Service, Elevation of Privilege).
*   **Output**: Defense-in-Depth Architecture Diagram.
*   **Control**: Architecture review must explicitly address segregation of duties and least privilege.

### 2.3. Design & Implementation Phase (Clause 5.4)
*   **Activity**: Secure Coding.
*   **Standards**: PEP 8 (Python), OWASP Top 10 mitigation guidelines.
*   **Tooling**:
    *   **SAST (Static Application Security Testing)**: Bandit (Python).
    *   **SCA (Software Composition Analysis)**: Safety / Dependabot.
*   **Control**: No code merge allowed without passing SAST and Linting checks (CI Pipeline).

### 2.4. Verification Phase (Clause 5.5)
*   **Activity**: Security Testing.
*   **Tooling**:
    *   **Unit Tests**: `pytest` covering security functions (auth, encryption).
    *   **Integrated Testing**: Test server environment checks.
*   **Control**: 100% Pass rate on security-critical unit tests.

### 2.5. Release Phase (Clause 5.8)
*   **Activity**: Artifact Hardening & signing.
*   **Output**: Immutable Container Images, SBOM.
*   **Control**: Image vulnerability scan (Trivy/Clair) before registry push.

---

## 3. Toolchain Configuration

The following tools are "Validated Tools" for the purpose of this plan:

| Tool | Purpose | Validation Status |
| :--- | :--- | :--- |
| **Visual Studio Code** | IDE, Linting | Standard Tool (No Val Required) |
| **GitHub Actions** | CI/CD Pipeline Orchestration | Validated (Config in Repo) |
| **Bandit** | Static Security Analysis | Validated (Version pinned) |
| **Safety** | Dependency Vulnerability Check | Validated (Version pinned) |
| **Docker** | Containerization | Standard Tool |

---

## 4. Software of Unknown Pedigree (SOUP) Management

*   **Definition**: Any third-party library (e.g., `fastapi`, `pydantic`).
*   **Entrance Criteria**:
    1.  License compatibility check (MIT/Apache/BSD).
    2.  Vulnerability check (Must be free of Critical/High CVEs).
    3.  Maintenance check (Must be actively maintained).
*   **Tracking**: `requirements.txt` acts as the source of truth for the SBOM.

---

## 5. Security Problem Resolution (Clause 9)

In the event of a vulnerability discovery:
1.  **Triage**: Assess impact using CVSS 3.1.
2.  **Plan**: Identify fix (patch, config change, workaround).
3.  **Verify**: Regression test the fix.
4.  **Release**: Hotfix deployment if Critical severity.

---

## 6. Traceability

| IEC 81001-5-1 Clause | MedAI Flow Implementation | Evidence |
| :--- | :--- | :--- |
| **5.1 Development Plan** | This Document | `IEC_81001_5_1_SECURITY_PLAN.md` |
| **5.2 Health Software Req.** | Security Requirements | `compliance/TEST_REPORT.md` |
| **5.3 Architecture** | System Config | `backend/app/config.py` |
| **5.4 Design & Imp.** | Codebase | `backend/app/` |
| **5.5 Verification** | Automated Tests | `tests/unit/` |
| **5.8 Release** | Docker release | `Dockerfile` |

---
**Approved By**: DevSecOps Lead
**Date**: 2026-01-08
