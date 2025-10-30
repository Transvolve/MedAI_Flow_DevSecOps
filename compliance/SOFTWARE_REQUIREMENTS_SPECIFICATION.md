# Software Requirements Specification (SRS)

## Scope
FastAPI microservice exposing endpoints for health, version, and AI inference on echocardiogram inputs.

## Functional Requirements
- Auth: Bearer token required for inference.
- Inference: Accepts video/image; returns EF estimate and HF classification (future).
- Observability: Structured logs, metrics, traces (future).

## Non-Functional Requirements
- Performance: p50/p95 latencies defined; cold-start budget.
- Reliability: Graceful failures, retries on downstream calls (future).
- Security: Least-privilege, non-root containers, SBOM, scans.

## Interfaces
- REST/JSON; OpenAPI published; versioned APIs.

## Constraints
- CPU baseline; optional GPU acceleration.
