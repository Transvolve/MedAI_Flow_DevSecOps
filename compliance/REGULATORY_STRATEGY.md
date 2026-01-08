# Regulatory Strategy & Cybersecurity Compliance Roadmap

**Document ID**: REG-STRAT-001  
**Version**: 1.0.0  
**Effective Date**: 2026-01-08  
**Status**: DRAFT  

---

## 1. Executive Summary

This document defines the cybersecurity regulatory strategy for the **MedAI Flow DevSecOps** platform. It establishes the framework for demonstrating "Reasonable Assurance of Safety and Effectiveness" (RASE) throughout the Total Product Life Cycle (TPLC), as required by global regulatory bodies including the US FDA, EU MDR, and other health authorities.

The strategy integrates compliance with the following primary standards:
*   **IEC 81001-5-1**: Health software and health IT systems safety, effectiveness and security (Process).
*   **ANSI/AAMI TIR57 & SW96**: Principles for medical device security - Risk management.
*   **NIST Cybersecurity Framework (CSF)**: Infrastructure and operational security baseline.
*   **FDA Premarket Guidance (2025)**: Content of Premarket Submissions for Management of Cybersecurity.

---

## 2. Regulatory Connectivity Map

We adopt a **Defense-in-Depth** and **Secure-by-Design** approach. The following table maps our operational artifacts to specific regulatory requirements.

| Regulatory Standard | Requirement | MedAI Flow Implementation | Artifact |
| :--- | :--- | :--- | :--- |
| **IEC 81001-5-1** | Secure Development Lifecycle | Github Actions CI/CD with automated security gates | `compliance/IEC_81001_5_1_SECURITY_PLAN.md` |
| **AAMI TIR57** | Security Risk Management | Threat Modeling (STRIDE) & Risk Analysis | `compliance/SECURITY_RISK_ANALYSIS.md` |
| **NIST CSF** | "Protect" & "Detect" Functions | Azure Key Vault, App Insights, AKS Hardening | `compliance/NIST_CSF_MAPPING.md` |
| **FDA 21 CFR 820** | Design Controls | Traceability Matrix & Automated Tests | `compliance/TEST_REPORT.md` |
| **ISO 27001** | Information Security Mgmt | Access Control, Operations Security | `compliance/iso_27001_security_controls.md` |

---

## 3. Product Security Framework

### 3.1. Secure Product Development Framework (SPDF)
We utilize a SPDF compliant with **IEC 81001-5-1**. This framework ensures security is not an "add-on" but an integral property of the software.

*   **Phase 1: Planning**: Threat Modeling (TIR57), Security Requirements Definition.
*   **Phase 2: Development**: Secure Coding Standards (Bandit SAST), Dependency Scanning (SOUP management).
*   **Phase 3: Verification**: Automated Security Testing (DAST), Unit Testing.
*   **Phase 4: Deployment**: Secure Configuration (Infrastructure as Code), SBOM Generation.
*   **Phase 5: Maintenance**: Vulnerability Management, Patching.

### 3.2. Security Risk Management (TIR57)
We distinguish between **Safety Risk** (harm to patient) and **Security Risk** (data breach, service denial).
*   *Security Risk* is evaluated using Exploitability (Common Vulnerability Scoring System - CVSS) and Impact.
*   High Impact Security Risks are mapped to Safety Hazards in the ISO 14971 Danger File.

---

## 4. Software of Unknown Pedigree (SOUP) Strategy

Third-party libraries represent a significant supply chain risk.
*   **Inventory**: We maintain a machine-readable SBOM (Software Bill of Materials) in SPDX/CycloneDX format.
*   **Monitoring**: Continuous dependency scanning via Github Dependabot and Safety.
*   **Maintenance**: Automated alerts for new CVEs in utilized packages.

---

## 5. Post-Market Surveillance (PMS) Plan

Compliance extends beyond release. Our PMS strategy includes:
1.  **Coordinated Vulnerability Disclosure (CVD)**: A public channel for researchers to report issues (security.txt).
2.  **Patch Management**: SLA-driven patching (Critical: <72h, High: <7 days).
3.  **Audit Logs**: Tamper-proof logging of all security-critical events (Login, Data Access, Admin Actions).

---

## 6. Approvals

| Role | Name | Signature | Date |
| :--- | :--- | :--- | :--- |
| **Head of Product Security** | *Pending* | | |
| **Regulatory Affairs** | *Pending* | | |
| **Lead Developer** | *Pending* | | |

---
**Confidentiality Notice**: This document contains proprietary compliance strategy info.
