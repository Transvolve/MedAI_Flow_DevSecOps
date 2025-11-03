**MedAI_Flow_DevSecOps — Secure Medical AI DevSecOps Platform:**
This repository demonstrates a secure, automated, and standards-compliant CI/CD pipeline for medical imaging AI software.
It integrates FastAPI, Azure Cloud (AKS + ACR), and GitHub Actions to showcase a production-grade, audit-ready DevSecOps workflow aligned with IEC 62304, ISO 13485, ISO 14971, ISO 27001, and FDA 21 CFR 820.

**Key Features:**
⚡ FastAPI backend for low-latency AI/ML model inference

🐳 Docker containerization for reproducible deployment

☁️ Terraform (IaC) to provision Azure resources (RG + ACR + AKS)

🔄 GitHub Actions CI/CD for automated build, test, and deployment

🔐 DevSecOps integration — linting, static analysis, and security scanning

📈 Scalable Kubernetes deployment with Azure AKS + LoadBalancer ingress

📜 Compliance templates for FDA and ISO documentation alignment

**Project Structure:**
MedAI_Flow_DevSecOps/
│
├── .flake8
├── .gitattributes
├── .github
│   └── workflows
│       └── main.yml                         # CI/CD pipeline
|
├── .gitignore
├── .venv
|
├── AZURE_CREDENTIALS.json
├── backend                                  # FastAPI backend source
│   ├── app
│   │   ├── config.yaml
│   │   ├── main.py
│   │   ├── middleware.py
│   │   ├── routes.py
│   │   ├── security.py
│   │   └── utils.py
│   └── Dockerfile
|
├── ci-cd
│   └── github-actions.yml
+ # (Optional)
+ # ci-cd/github-actions.yml — legacy or sample workflow, not used in production pipeline
├── compliance                               # Regulatory documentation templates
│   ├── fda_21cfr820_traceability_matrix.md
│   ├── iso_27001_security_controls.md
│   ├── iso_62304_lifecycle_plan.md
│   └── risk_management_summary.md
|
├── docs                                    # Architecture & visual documentation
│   ├── architecture_diagram.png
│   ├── debug.txt
│   ├── latency_scaling_summary.md
│   └── pipeline_flow.png
|
├── infra                                  # Infrastructure and scripts
│   ├── aks_deploy.yaml                    # Kubernetes deployment manifest
│   ├── ingress.yaml
│   ├── scripts
│   │   └── verify_acr_access.ps1          # PowerShell ACR verification script
│   ├── storage.yaml
│   └── terraform                          # Azure IaC provisioning
│       ├── .terraform
│       ├── .terraform.lock.hcl
│       ├── main.tf
│       └── terraform.tfstate
|
├── ml                                    # AI model modules (future integration)
│   ├── cache_manager.py
│   ├── inference.py
│   └── preprocess.py
|
├── notebooks
├── README.md
└── tests
    ├── test_api.py
    ├── test_model.py
    └── test_security.py

**CI/CD Pipeline Overview**
Every **push or PR to `main`** triggers the following automated stages  
(GitHub Actions → [`.github/workflows/main.yml`](.github/workflows/main.yml)):

     Stage	          ||           Purpose	                      ||      Tools	    ||  Status
✅ Lint & Security Scan ||  Enforces coding standards and static       ||  flake8, bandit     ||  Passed
                         ||      security analysis                     ||                     ||  Passed
✅ Unit Tests           ||  Validates API logic and integration	     || pytest, FastAPI     ||  Passed
                         ||                                            ||    TestClient        ||  
✅ Build & Push	        || Builds and publishes Docker images          || Docker, az acr login || Passed
                         ||  to Azure Container Registry (ACR)	      ||                      ||
✅ Deploy	             ||  Deploys application to Azure Kubernetes    ||  kubectl, az aks	    ||  Passed
                         || Service (AKS) and verifies rollout	      ||                      ||

📊 All jobs run in GitHub-hosted Ubuntu runners — no local Docker required.
Pip caching is enabled to reduce CI runtime by >30%.

**How to Review and Run This Project:**
For Reviewers (No Setup Required)

     1. Visit the repository’s Actions tab to see all four CI/CD stages passing (green checkmarks).

     2. Review logs, code, and documentation directly from GitHub — no local setup, Docker, or Azure login required.

# For Local Testing (Optional):
You can run the FastAPI backend locally without Docker or Azure.

```bash
# Clone the repository
git clone https://github.com/Transvolve/MedAI_Flow_DevSecOps.git
cd MedAI_Flow_DevSecOps/backend

# Install dependencies (includes FastAPI, Uvicorn, Pytest, Flake8, Bandit)
pip install -r ../requirements-ci.txt

# Run the FastAPI app
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

# Access locally at:
http://127.0.0.1:8080/health
http://127.0.0.1:8080/version
http://127.0.0.1:8080/docs

# Tip: If your IDE or terminal warns that packages like uvicorn, flake8, pytest, or bandit are not installed, ensure the correct Python environment is activated and re-run the pip install command above.

# For CI/CD Reference

The automated GitHub Actions pipeline installs the same dependencies from requirements-ci.txt during every run to guarantee consistent environments between local testing and the hosted runner.

**Code & Architecture:**
Browse source code, Terraform scripts, and CI/CD workflows to see how automation and compliance are integrated.

**Container & Deployment (Cloud)**
All container builds and deployments occur automatically in the pipeline:
1. Build image → push to Azure Container Registry (medaiflowacr)
2. Deploy container → Azure Kubernetes Service (rg-medai-flow)
3. Rollout verification via kubectl rollout status
4. Azure RBAC validation via infra/scripts/verify_acr_access.ps1

**Infrastructure as Code**
Terraform (infra/terraform) provisions:
1. Azure Resource Group (rg-medai-flow)
2. Azure Container Registry (ACR)
3. Azure Kubernetes Service (AKS)
State files & secrets are excluded from version control.
Secrets handled via GitHub Secrets and Azure Key Vault.

**Security & Compliance Notes:**
* No personal credentials or Terraform state files are committed.
* Environment variables and secrets are managed via GitHub Secrets and Azure Key Vault.
* Security scanning (bandit, flake8) is integrated into the CI/CD pipeline.
* Project artifacts follow IEC 62304 lifecycle and ISO 27001 security controls templates.

**Security & Compliance Highlights**
| Control Area                 | Implementation                   | Reference                                         |
| ---------------------------- | -------------------------------- | ------------------------------------------------- |
| **Secure Coding**            | Linting + Static Scan            | `flake8`, `bandit`                                |
| **Credential Management**    | GitHub Secrets + Azure Key Vault | `.github/workflows/main.yml`                      |
| **Infrastructure Integrity** | Terraform IaC                    | `/infra/terraform`                                |
| **Software Lifecycle**       | IEC 62304-compliant docs         | `/compliance/iso_62304_lifecycle_plan.md`         |
| **Risk Management**          | ISO 14971 mapping                | `/compliance/risk_management_summary.md`          |
| **Traceability**             | CFR 21 Part 820 Matrix           | `/compliance/fda_21cfr820_traceability_matrix.md` |


**Summary:**
| Area               | Technology                     | Purpose                             |
| ------------------ | ------------------------------ | ----------------------------------- |
| **Infrastructure** | Terraform + Azure AKS/ACR      | Automated provisioning              |
| **Application**    | Python 3.11 / FastAPI          | Medical imaging backend             |
| **CI/CD**          | GitHub Actions                 | Continuous Integration + Deployment |
| **Security**       | Bandit / Flake8 / RBAC         | DevSecOps Compliance                |
| **Compliance**     | ISO 13485, 62304, 14971, 27001 | Medical Software Lifecycle          |

**Demo Instructions**
1. Open the repository → Actions tab
     → Show all 4 pipeline stages are green.

2. Open .github/workflows/main.yml
     → Explain each stage (lint, test, build, deploy).

3. Show /infra/scripts/verify_acr_access.ps1
     → Demonstrate Azure authentication verification.

4. Open /compliance/iso_62304_lifecycle_plan.md
     → Show traceability and lifecycle documentation.

5. (Optional): Run locally → uvicorn app.main:app
     → Show /health and /version endpoints live.

**Branching & Testing Workflow**
Branch	                         Purpose
main	                    Stable production-ready pipeline
feature/*	               Experimental branches for testing & new features

Typical flow:
git checkout -b feature/test-latency-fix
# make edits → commit → push
git push -u origin feature/test-latency-fix
# then open PR → merge into main → auto CI/CD run

Manual triggers also available via Run workflow button (workflow_dispatch).

**Next Steps (Phase 2–6 Roadmap — Latency, Reliability & Scalability Focus)**
| Phase | Focus Area                                | Objective                                            |
| **2** | Performance & Latency Optimization        | Reduce inference and API response times              |
| **3** | Reliability & Observability               | Improve fault-tolerance and system health visibility |
| **4** | Scalability & Resource Optimization       | Enable dynamic workload scaling and efficiency       |
| **5** | Modular Architecture Alignment            | Strengthen interfaces and module boundaries          |
| **6** | Advanced Security & Compliance Automation | Mature DevSecOps posture and continuous compliance   |

🔹 Phase 2 — Performance & Latency Optimization:

1. Implement async FastAPI routes and optimize I/O
2. Profile model inference with asyncio, uvloop
3. Add caching layer (Redis / LRU) for repeat inference
4. Benchmark latency under concurrent load (locust, k6)

🔹 Phase 3 — Reliability & Observability:

1. Integrate OpenTelemetry tracing & structured logging
2. Add liveness/readiness probes in AKS manifests
3. Implement retry logic for transient failures
4. Deploy Prometheus + Grafana dashboards

🔹 Phase 4 — Scalability & Resource Optimization

1. Enable Horizontal Pod Autoscaler (HPA) in AKS
2. Optimize Docker image size & cold-start time
3. Add message queue (Azure Service Bus / RabbitMQ) for async jobs
4. Introduce model batching to improve GPU/CPU utilization

🔹 Phase 5 — Modular Architecture Alignment:

1. Define explicit API contracts with OpenAPI schemas
2. Split backend into micro-modules (auth, inference, analytics, storage)
3. Adopt Domain-Driven Design (DDD) for service boundaries
4. Introduce versioned API gateway for modular releases

🔹 Phase 6 — Advanced Security & Compliance Automation:

1. Integrate SBOM + Trivy vulnerability scanning
2. Add secret scanning (Gitleaks) in CI/CD
3. Automate traceability matrix updates via scripts
4. Sign & attest containers (Cosign / Sigstore)

**License**
This project will be released under the MIT License (LICENSE file to be added in the next update).

**Contributions:**
Contributions and extensions (e.g., model training, advanced monitoring, IaC enhancements) are welcome via pull requests.
Please ensure commits maintain compliance traceability and secure coding standards.

**Author**
Dr. Mehul Pancholi, PhD (Biomedical Engineering)
Senior System & Software Engineer | Embedded IoT | AI/ML | Medical Device DevSecOps
London, UK | LinkedIn: https://www.linkedin.com/in/mehul-pancholi-284453b/ 
