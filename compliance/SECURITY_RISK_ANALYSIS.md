# Security Risk Analysis & Management Report

**Document ID**: SRA-TIR57-001  
**Version**: 1.0.0  
**Compliance**: AAMI TIR57, ANSI/AAMI SW96, ISO 14971  

---

## 1. Scope & Methodology

This document constitutes the **Security Risk Management File** for MedAI Flow. It follows the process defined in **AAMI TIR57: Principles for medical device security - Risk management**.

The methodology involves:
1.  **Asset Identification**: What are we protecting?
2.  **Threat Modeling**: What can go wrong? (STRIDE)
3.  **Risk Assessment**: Probability x Severity (Pre-Mitigation).
4.  **Risk Control**: Mitigation measures.
5.  **Residual Risk Evaluation**: Is the remaining risk acceptable?

---

## 2. Asset Inventory

| Asset ID | Asset Name | CIA Priority | Description |
| :--- | :--- | :--- | :--- |
| **AST-01** | Patient Health Information (PHI) | Conf > Int > Avail | Sensitive user medical data. |
| **AST-02** | Authentication Tokens (JWT) | Conf > Int | Keys granting access to the API. |
| **AST-03** | AI Inference Engine | Int > Avail | The core logic processing data. |
| **AST-04** | Audit Logs | Int > Avail | Legal record of system activity. |
| **AST-05** | Admin Credentials | Conf > Int | Root access to infrastructure. |

---

## 3. Threat Modeling (STRIDE)

| Threat ID | Type | Asset | Description |
| :--- | :--- | :--- | :--- |
| **T-01** | **S**poofing | AST-02 | Attacker forges a JWT to impersonate a doctor. |
| **T-02** | **T**ampering | AST-04 | Attacker modifies audit logs to hide malicious activity. |
| **T-03** | **R**epudiation | AST-03 | User denies performing an action; missing logs prevent proof. |
| **T-04** | **I**nformation Disclosure | AST-01 | SQL Injection leaks patient records. |
| **T-05** | **D**enial of Service | AST-03 | API flooded with requests, freezing the service. |
| **T-06** | **E**levation | AST-05 | Regular user exploits bug to gain Admin rights. |

---

## 4. Risk Assessment & Control Table

**Scoring Key**:
*   **Severity (S)**: 1 (Negligible) to 5 (Catastrophic/Death).
*   **Probability (P)**: 1 (Improbable) to 5 (Frequent).
*   **Risk Level (R)**: S * P. (Low < 6, Med 6-12, High > 12).

| Threat ID | Pre-Mitigation Score (S x P = R) | Risk Control Measure | Implementation | Post-Mitigation Score (S x P = R) | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **T-01** | 4 x 4 = **16 (HIGH)** | Strong cryptographic signing (HS256) + Secret Rotation | `config.py`: `ALGORITHM`, `SECRET_KEY` | 4 x 1 = **4 (LOW)** | ✅ Acceptable |
| **T-02** | 3 x 3 = **9 (MED)** | Immutable Audit Logs / Write-once storage | `infra`: Azure Monitor Locks | 3 x 1 = **3 (LOW)** | ✅ Acceptable |
| **T-03** | 3 x 2 = **6 (MED)** | Comprehensive Logging of all API calls | `middleware`: LoggingMiddleware | 3 x 1 = **3 (LOW)** | ✅ Acceptable |
| **T-04** | 5 x 3 = **15 (HIGH)** | ORM Usage (SQLAlchemy) + Input Validation (Pydantic) | `backend/app/models`, `schemas` | 5 x 1 = **5 (LOW)** | ✅ Acceptable |
| **T-05** | 2 x 4 = **8 (MED)** | Rate Limiting (Redis) | `backend/app/main.py`: Limiter | 2 x 1 = **2 (LOW)** | ✅ Acceptable |
| **T-06** | 5 x 2 = **10 (MED)** | RBAC (Role Based Access Control) | `backend/app/auth.py`: Scopes | 5 x 1 = **5 (LOW)** | ✅ Acceptable |

---

## 5. Cybersecurity-Safety Interlock

This section maps Security Risks to ISO 14971 Safety Hazards.

*   **Cyber Event**: T-04 (Data Corruption of AI input).
*   **Safety Impact**: AI returns incorrect diagnosis.
*   **Safety Hazard ID**: HZ-003 (Incorrect Diagnostic Output).
*   **Mitigation**: Input Integrity Check (hashing) before processing.

---

## 6. Conclusion and Benefit-Risk Analysis

All identified security risks have been mitigated to an acceptable level (ALARP - As Low As Reasonably Practicable). The benefits of the device (improving diagnostic workflow) outweigh the residual cybersecurity risks.

**Risk Management Lead**: DevSecOps Team
**Review Date**: 2026-01-08
