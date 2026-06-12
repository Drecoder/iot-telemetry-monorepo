# IoT Fleet Telemetry Monorepo

A production-ready, full-stack cloud monorepo designed to ingest, validate, and persist high-volume, real-time time-series telemetry data from a globally distributed fleet of 20,000 concurrent autonomous robots.

[![Status: Production](https://img.shields.io/badge/Status-Production-green)]()
[![Last Audit](https://img.shields.io/badge/Last%20Audit-June%202026-blue)]()
[![Success Rate](https://img.shields.io/badge/Audit%20Success-96.4%25-brightgreen)]()
[![Cost](https://img.shields.io/badge/Cost-$0-orange)]()

This project implements a unified architecture combining **Cloud Platform Engineering (Infrastructure as Code, Hardened Containers, Service Mesh, CI/CD)** with **Software Engineering (TypeScript, Node.js, Express)** under a single, cohesive source of truth.

---

## 🏗️ Architectural Overview

The system handles streaming edge data by decoupling the ingress layer from the persistence layer to maintain low latencies, smooth out seasonal traffic bursts, and ensure high availability:

* **Ingress Layer:** An AWS Application Load Balancer (ALB) handles SSL/TLS termination and routes inbound JSON payloads over HTTPS securely to the compute layer.
* **Service Mesh Data Plane:** An Istio-managed infrastructure layer automatically injects sidecar proxies (**Envoy**) to abstract traffic management, enforce zero-trust **mutual TLS (mTLS)** mutual encryption across pod boundaries natively, and provide deep trace analysis without modifying application runtimes.
* **Stream Ingestion Buffer:** An Amazon Kinesis Data Stream configured in **`ON_DEMAND`** allocation mode natively cushions the platform against massive real-time IoT traffic shocks without requiring manual shard capacity management or risking throughput throttling.
* **Compute Layer:** High-throughput TypeScript/Node.js REST microservices packaged in minimalist, non-root multi-stage Docker containers (`node:20-alpine`). Workers ingest, validate, and parse stream packets using structured `pino` logging outputs. Orchestrated inside isolated private subnets.
* **Persistence Layer:** Amazon DynamoDB serves as the transactional time-series datastore, utilizing a distributed partition key (`robotId`) and chronological sort key (`timestamp`) to complete concurrent writes at scale.
* **Infrastructure as Code (IaC):** Explicit cloud topologies and architectural guardrails declared completely using modular, test-driven Terraform blueprints.

---

## 📂 Repository Structure

The monorepo uses standard workspaces to keep applications, packages, and operational layers strictly separated yet perfectly synchronized:

```text
cnh-telemetry-monorepo/
├── .github/workflows/
│   └── ci-cd.yml          # GitHub Actions CI/CD automation pipeline
├── apps/
│   ├── processor-alerts/  # Anomaly detection processor microservice
│   ├── processor-storage/ # Stream-to-DynamoDB decoupled ingestion processor
│   └── telemetry-api/     # TypeScript Edge Ingestion HTTP API & Dockerfile
├── infra/
│   ├── k8s/
│   │   └── telemetry-ingestor.yaml # Environment-agnostic Kubernetes deployment
│   └── terraform/         # Declarative AWS Blueprints (VPC, Kinesis, DynamoDB)
│       ├── messaging.tf   # On-Demand Kinesis Stream configurations
│       └── tests/         # Native HCL infrastructure plan assertions
├── packages/
│   └── shared-types/      # Centralized invariant data contracts and schemas
├── Makefile               # Local development task runner orchestrator
├── package.json           # Root npm workspaces definition
└── tsconfig.base.json     # Global shared TypeScript configuration rules
🔍 Architecture Audit (June 2026)
A comprehensive architecture audit was performed using a local 7B AI model (Qwen 2.5 Coder) across 28 files, achieving a 96.4% success rate. The audit analyzed 5 different architectural lenses: CHAOS (failure analysis), BLAST (blast radius), GOVERNANCE (configuration), JSON_CONFIG, and SIMPLE.

Overall Health Assessment
Layer	Status	Key Findings
Ingest Services	🔴 Critical	Missing error handling, no input validation, missing environment variables
Infrastructure	🟠 Warning	Missing security groups, implicit dependencies, variable risks
Configs	🟠 Warning	Overly broad patterns (**), missing linting rules, relative path dependencies
Business Logic	🟡 Attention	Limited documentation, inconsistent naming conventions
Top 5 Critical Issues
Rank	Issue	Layer	Priority
1	Missing error handling and logging	Ingest Services	P0
2	Missing environment variables (AWS_REGION, TABLE_NAME)	Ingest Services	P0
3	Missing security groups/NACLs on subnets	Infrastructure	P0
4	Overly broad patterns (**) in config files	Configs	P1
5	Implicit dependencies between Terraform resources	Infrastructure	P1
Immediate Fixes (Week 1)
Task	Layer	Effort
Add error handling and logging to API endpoints	telemetry-api	M
Set TABLE_NAME environment variable	processor-storage	S
Configure AWS_REGION properly	All services	S
Implement network ACLs and security groups	Terraform	M
Add strictNullChecks to tsconfig.base.json	Configs	S
🚀 Local Development & Toolchain
A root-level Makefile handles cross-OS translation loops, abstracting away individual runtime scripts into clean unified macros. Ensure you have Node.js (v20+), Docker Desktop, Istio (v1.30+), and Terraform (v1.5+) installed locally.

1. Initialize Project & Workspaces
Install all node module dependencies cleanly across every internal npm workspace branch:

bash
make install
2. Execute Full Toolchain Pipeline
Trigger the complete verification and deployment sequence. This single command installs dependencies, runs application unit tests, runs Terraform plan assertions, executes a Checkov SAST security scan, builds your Docker container, handles cross-OS image injection, and applies the manifest directly onto your local Minikube cluster:

bash
make
3. Run Validation Gateways Individually
If you want to isolate specific validation sweeps without building images or deploying changes, run the specialized testing blocks:

All Quality Gates: make test (Runs application tests, infrastructure assertions, and security scans sequentially)

Application Code Tests: make test-app (Runs TypeScript API and worker unit tests via Jest)

Infrastructure Assertions: make test-infra (Executes native Terraform syntax and configuration plan validation checks)

Security Scanning: make security-scan (Launches a Checkov Static Infrastructure Security Scan via Docker)

Code Coverage Insights: make coverage (Generates application code coverage tables and maps HTML reports to coverage/lcov-report/index.html)

4. Isolated Cluster Deployment Operations
Manage your local development Kubernetes environments explicitly using the cross-OS WSL2-to-Windows host bridge commands:

bash
make dev-build    # Compiles the telemetry-ingestor container inside WSL
make dev-load     # Wirelessly loads the container cache into Minikube's engine
make dev-deploy   # Applies the environment-agnostic YAML and streams live pod updates
make dev-clean    # Drops the ingestor pods out of your local cluster smoothly
5. Reset Workspace Assets
Strip local code coverage caches, compiled JavaScript outputs, local hidden Terraform provider modules, and running cluster deployment resources simultaneously to restore a pristine directory state:

bash
make clean
⛵ Service Mesh Integration (Istio & Kiali)
The repository leverages an Istio Service Mesh platform layer to manage internal traffic abstractions and live tracing telemetry maps.

1. Environment Initialization
To ensure strict structural compatibility between Windows hosts and virtualization containers under WSL2, binaries must run out of native Linux filesystem storage (~/).

Execute the initial platform control-plane setup within your WSL2 Terminal:

bash
# Pull down clean Linux binary package targets natively
cd ~ && curl -L https://istio.io/downloadIstio | sh -

# Map target paths to your Linux active shell profile
echo 'export PATH="$HOME/istio-1.30.0/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc

# Confirm native validation checks pass
istioctl version --remote=false
2. Mesh Deployment & Automatic Sidecar Injection
Apply the mesh topology configuration to your running Minikube container runtime environment and label the workspace namespace to trigger transparent Envoy proxy nesting on pod initialization (2/2 READY state execution):

bash
# 1. Install Istio core system components onto the cluster profile
istioctl install --set profile=demo -y

# 2. Instruct the default namespace context to inject sidecar proxies automatically
kubectl label namespace default istio-injection=enabled --overwrite

# 3. Perform a zero-downtime cluster rolling restart to bundle data planes
kubectl rollout restart deployment/telemetry-ingestor
3. Access Traffic Graphs (Kiali Dashboard)
Launch the visual web control interface to trace real-time packet latency distributions, request streams, and live deployment dependency graphs:

bash
istioctl dashboard kiali
(WSL Bridge Note: Ctrl+Click the terminal output url http://localhost:20001/kiali to interact with your live architecture dashboard natively through your Windows web browser).

⚙️ Automated Quality Gates (CI/CD)
Any pull request or push code modification targeted at the main branch triggers the automated verification pipeline inside .github/workflows/ci-cd.yml. The runner guarantees a high stability baseline by enforcing:

Dependency Alignment: Verifies and locks sub-workspace trees cleanly.

Software Verification: Re-runs Jest unit validations across all applications to shield against regression bugs.

IaC Linting: Audits Terraform configuration patterns via terraform fmt.

Architectural Compliance: Natively evaluates structural cloud logic via terraform test to ensure infrastructure schemas strictly match cloud provider requirements before allowing continuous delivery state promotions.

📊 Audit Artifacts
The following architecture audit reports are available in analysis_reports/:

Artifact	Description	Audience
MASTER_ARCHITECTURE_REPORT.md	Complete 35.9 KB technical audit	Engineers, Architects
EXECUTIVE_SUMMARY.md	Leadership overview with top 5 issues	CTO, VP Engineering
REMEDIATION_ROADMAP.md	Week-by-week fix plan	Engineering Managers
📋 Next Steps
Based on the June 2026 architecture audit:

Week 1: Implement P0 fixes (error handling, environment variables, security groups)

Week 2-4: Add input validation, linting rules, and coverage thresholds

Monthly: Re-run the audit to track improvement