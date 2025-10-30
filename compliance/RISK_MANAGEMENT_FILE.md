# Risk Management File (ISO 14971)

## Hazards
- R-SEC-001: Unauthorized access to inference endpoint.
  - Controls: Bearer token auth; secrets management; logging.
- R-OPS-001: Service downtime.
  - Controls: Health/readiness; K8s probes; autoscaling (future).
- R-PERF-001: Excessive latency.
  - Controls: ONNX Runtime; profiling; perf tests (future).

## Residual Risk
- Acceptable for pilot/non-diagnostic use only.
