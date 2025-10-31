# Product Requirements Specification (PRS)

- Product: MedAI Flow – Echocardiogram AI Inference Service
- Intended Use: Assist clinicians by estimating EF and flagging potential heart failure risk from echocardiogram views.
- Users: Cardiologists, sonographers, clinical IT.
- Environment: Hospital on-prem / cloud (AKS), API-first.

## Key Requirements
- Low-latency inference (target p50 < 150ms, p95 < 400ms on CPU-only).
- High availability (SLO 99.9%).
- Secure data handling; PHI avoidance by default; audit logs.
- Versioned models and traceable datasets.

## Acceptance Criteria
- Health, readiness endpoints; authenticated inference.
- Reproducible model artifacts; SBOM and container scans pass.
- Logging/metrics/traces exposed for operations.

## Contraindications and Warnings
- Not a diagnostic device; clinical oversight required.
