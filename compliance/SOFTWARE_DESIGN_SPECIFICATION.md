# Software Design Specification (SDS)

## Architecture
- FastAPI + Uvicorn ASGI app.
- Inference engine with ONNX Runtime (future).
- Azure AKS deployment via GitHub Actions.

## Modules
- `app.main`: app wiring, health/version.
- `app.routes`: protected inference endpoint.
- `app.security`: token validation.
- `app.utils`: latency middleware/decorator.

## Data Flow
Request -> Auth -> Preprocess -> Inference -> Postprocess -> Response.

## Error Handling
Standardized error payload; HTTP codes; structured logs (future).
