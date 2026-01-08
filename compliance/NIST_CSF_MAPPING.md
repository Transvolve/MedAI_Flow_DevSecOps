# NIST Cybersecurity Framework (CSF) Mapping

**Document ID**: NIST-CSF-MAP-001  
**Version**: 1.0.0  
**Framework Version**: NIST CSF 1.1 / 2.0  

---

## 1. Overview

This document demonstrates the alignment of the MedAI Flow DevSecOps platform with the **NIST Cybersecurity Framework**. It maps the five core functions (Identify, Protect, Detect, Respond, Recover) to implemented technical and process controls.

---

## 2. Core Function Mapping

### Function: IDENTIFY (ID)
*Develop an organizational understanding to manage cybersecurity risk to systems, people, assets, data, and capabilities.*

| Category | Subcategory | MedAI Flow Implementation | Evidence |
| :--- | :--- | :--- | :--- |
| **Asset Management (ID.AM)** | Data & devices are inventoried | SBOM generated for all builds; Asset list in Risk Analysis. | `SECURITY_RISK_ANALYSIS.md` |
| **Governance (ID.GV)** | Cyber policies established | Regulatory Strategy and Security Plans defined. | `REGULATORY_STRATEGY.md` |
| **Risk Assessment (ID.RA)** | Risk assessed | STRIDE Threat Modeling conducted. | `SECURITY_RISK_ANALYSIS.md` |
| **Supply Chain (ID.SC)** | Third-party risks managed | Automated dependency scanning (Safety/Dependabot). | `IEC_81001_5_1_SECURITY_PLAN.md` |

### Function: PROTECT (PR)
*Develop and implement appropriate safeguards to ensure delivery of critical services.*

| Category | Subcategory | MedAI Flow Implementation | Evidence |
| :--- | :--- | :--- | :--- |
| **Access Control (PR.AC)** | Access rights managed | Role-Based Access Control (RBAC) & MFA policies. | `backend/app/auth.py` |
| **Data Security (PR.DS)** | Data-at-rest/transit protected | TLS 1.2+ forced; Argon2id hashing; Database encryption. | `backend/app/config.py` |
| **Maintenance (PR.MA)** | Remote maintenance secure | CI/CD pipeline used for all changes; no direct SSH. | `.github/workflows/` |
| **Protective Tech (PR.PT)** | Audit/Log records determined | Immutable logging configuration; Rate limiting. | `backend/app/main.py` |

### Function: DETECT (DE)
*Develop and implement appropriate activities to identify the occurrence of a cybersecurity event.*

| Category | Subcategory | MedAI Flow Implementation | Evidence |
| :--- | :--- | :--- | :--- |
| **Anomalies (DE.AE)** | Anomalies detected | Rate limit alerts; Failed login spike detection. | Azure Monitor Alerts |
| **Monitoring (DE.CM)** | Malicious code detected | Container scanning; Static Analysis (Bandit). | Test Reports |

### Function: RESPOND (RS)
*Develop and implement appropriate activities to take action regarding a detected cybersecurity incident.*

| Category | Subcategory | MedAI Flow Implementation | Evidence |
| :--- | :--- | :--- | :--- |
| **Planning (RS.RP)** | Response plan executed | Incident Response Playbook (part of ISO 27001). | `compliance/iso_27001_security_controls.md` |
| **Analysis (RS.AN)** | Incidents analyzed | Audit logs provide forensic trail. | `compliance/PHASE1_SECURITY_AUDIT.md` |
| **Mitigation (RS.MI)** | Incidents contained | Token Revocation (Blacklist) capability. | `backend/app/auth.py` |

### Function: RECOVER (RC)
*Develop and implement appropriate activities to maintain plans for resilience and to restore any capabilities or services involved in a cybersecurity incident.*

| Category | Subcategory | MedAI Flow Implementation | Evidence |
| :--- | :--- | :--- | :--- |
| **Recovery Planning (RC.RP)** | Recovery plan executed | Infrastructure as Code (Terraform) allows rapid rebuild. | `infra/terraform/` |
| **Improvements (RC.IM)** | Plans updated | Post-incident reviews fed back into Risk Assessment. | `SECURITY_RISK_ANALYSIS.md` |

---

## 3. Compliance Summary

MedAI Flow successfully addresses the core intent of all 5 NIST CSF Functions. The platform leverages modern DevSecOps automation ("Protect", "Detect") to ensure high resilience and rapid recovery ("Recover").

**Assessor**: DevSecOps Team
**Date**: 2026-01-08
