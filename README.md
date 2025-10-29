MedAI_Flow_DevSecOps:

Developed by Dr. Mehul Pancholi, Senior System & Software Engineer with 20+ years of experience in DevSecOps, Embedded IoT, AI/ML, and Medical Device Systems & Software Engineering.

This repository demonstrates a secure, scalable, and compliant DevSecOps pipeline for medical imaging software, integrating AI/ML inference, cloud infrastructure automation, and software lifecycle governance aligned with IEC 62304, ISO 13485, ISO 14971, ISO 27001, and 21 CFR 820.

Key Features:

FastAPI backend for low-latency high-performance AI/ML model inference

Docker containerization for reproducible deployment

Terraform (IaC) provisioning of Azure resources (AKS + ACR) - manage Azure Infrastructure

GitHub Actions for automated CI/CD

Static and dynamic security analysis tools for DevSecOps maturity

Logging, telemetry, and compliance placeholders for medical-grade traceability

Scalable Kubernetes deployment (AKS with LoadBalancer ingress)

Project Structure:
MedAI_Flow_DevSecOps/
│
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entrypoint
│   │   ├── routes.py            # Modular endpoints
│   │   ├── security.py          # JWT + encryption + OWASP validation
│   │   ├── middleware.py        # Logging + latency tracking
│   │   └── config.yaml
│   └── Dockerfile               # Multi-stage container build
│
├── ml/
│   ├── preprocess.py            # Preprocessing pipeline
│   ├── inference.py             # Model loading & inference
│   └── cache_manager.py         # Caching layer for performance
│
├── infra/
│   ├── terraform/               # Infrastructure as Code
│   │   └── main.tf
│   ├── aks_deploy.yaml          # Kubernetes deployment spec
│   ├── ingress.yaml             # API Gateway ingress
│   └── storage.yaml             # Persistent volume claims
│
├── ci-cd/
│   └── github-actions.yml       # GitHub Actions CI/CD workflow
│
├── compliance/
│   ├── iso_62304_lifecycle_plan.md
│   ├── iso_27001_security_controls.md
│   ├── fda_21cfr820_traceability_matrix.md
│   └── risk_management_summary.md
│
├── docs/
│   ├── architecture_diagram.png
│   ├── pipeline_flow.png
│   └── latency_scaling_summary.md
│
├── tests/
│   ├── test_api.py
│   ├── test_model.py
│   └── test_security.py
│
├── requirements.txt
├── README.md
└── LICENSE

How to Review and Run This Project:

This repository demonstrates a secure, cloud-native DevSecOps pipeline for medical imaging AI software, built using:

Python 3.11 / FastAPI

Azure AKS + ACR

Terraform

GitHub Actions

Docker

Security and compliance alignment with major medical software standards.

Reviewer Guidance:

You do not need to install Docker Desktop or Azure locally to review this project.

Code & Architecture:
Browse source code, Terraform scripts, and CI/CD workflows to see how automation and compliance are integrated.

Pipeline Execution:
The GitHub Actions workflow (ci-cd/github-actions.yml) automatically:

Lints and tests the backend code

Builds and pushes container images to Azure Container Registry

Deploys to Azure Kubernetes Service (AKS)

→ All steps run in GitHub-hosted runners — no local Docker required.

Infrastructure Deployment:
Terraform under infra/terraform provisions the entire Azure stack (RG + ACR + AKS).
Sensitive state files and credentials are excluded from version control.

Optional Local Run:

If you wish to run the backend locally:

git clone https://github.com/Transvolve/MedAI_Flow_DevSecOps.git
cd MedAI_Flow_DevSecOps/backend
docker build -t medai_backend .
docker run -p 8080:8080 medai_backend


Then visit http://localhost:8080
.

Security & Compliance Notes:

No personal credentials or Terraform state files are committed.

Environment variables and secrets are managed via GitHub Secrets and Azure Key Vault.

Security scanning (bandit, flake8) is integrated into the CI/CD pipeline.

Project artifacts follow IEC 62304 lifecycle and ISO 27001 security controls templates.

Summary:
     Area	      ||             Technology	                 ||               Purpose
Infrastructure    ||	Terraform + Azure AKS/ACR            ||    Automated provisioning
Application	      ||    Python 3.11 / FastAPI	             ||    Medical imaging backend
CI/CD	          ||    GitHub Actions	                     ||    Continuous Integration + Deployment
Security	      ||    Bandit / Flake8 / Secrets Scan	     ||    DevSecOps Compliance
Compliance	      ||    ISO 13485, 62304, 14971, 27001	     ||    Medical Software Lifecycle

License:

Released under the MIT License — see the LICENSE
 file for details.

Contributions:

Contributions and extensions (e.g., model training, advanced monitoring, IaC enhancements) are welcome via pull requests.