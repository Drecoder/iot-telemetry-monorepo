```markdown
# IoT Fleet Telemetry Monorepo

A production-ready, full-stack cloud monorepo designed to ingest, validate, and persist high-volume, real-time time-series telemetry data from a globally distributed fleet of 20,000 concurrent autonomous robots.

This project implements a unified architecture combining **Cloud Platform Engineering (Infrastructure as Code, Hardened Containers, CI/CD)** with **Software Engineering (TypeScript, Node.js, Express)** under a single, cohesive source of truth.

## 🏗️ Architectural Overview

The system handles streaming edge data by decoupling the ingress layer from the persistence layer to maintain low latencies, smooth out seasonal traffic bursts, and ensure high availability:

* **Ingress Layer:** An AWS Application Load Balancer (ALB) handles SSL/TLS termination and routes inbound JSON payloads over HTTPS securely to the compute layer.
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

```

---

## 🚀 Local Development & Toolchain

A root-level `Makefile` handles cross-OS translation loops, abstracting away individual runtime scripts into clean unified macros. Ensure you have Node.js (v20+), Docker Desktop, and Terraform (v1.5+) installed locally.

### 1. Initialize Project & Workspaces

Install all node module dependencies cleanly across every internal npm workspace branch:

```bash
make install

```

### 2. Execute Full Toolchain Pipeline

Trigger the complete verification and deployment sequence. This single command installs dependencies, runs application unit tests, runs Terraform plan assertions, executes a Checkov SAST security scan, builds your Docker container, handles cross-OS image injection, and applies the manifest directly onto your local Minikube cluster:

```bash
make

```

### 3. Run Validation Gateways Individually

If you want to isolate specific validation sweeps without building images or deploying changes, run the specialized testing blocks:

* **All Quality Gates:** `make test` (Runs application tests, infrastructure assertions, and security scans sequentially)
* **Application Code Tests:** `make test-app` (Runs TypeScript API and worker unit tests via Jest)
* **Infrastructure Assertions:** `make test-infra` (Executes native Terraform syntax and configuration plan validation checks)
* **Security Scanning:** `make security-scan` (Launches a Checkov Static Infrastructure Security Scan via Docker)
* **Code Coverage Insights:** `make coverage` (Generates application code coverage tables and maps HTML reports to `coverage/lcov-report/index.html`)

### 4. Isolated Cluster Deployment Operations

Manage your local development Kubernetes environments explicitly using the cross-OS WSL2-to-Windows host bridge commands:

```bash
make dev-build    # Compiles the telemetry-ingestor container inside WSL
make dev-load     # Wirelessly loads the container cache into Minikube's engine
make dev-deploy   # Applies the environment-agnostic YAML and streams live pod updates
make dev-clean    # Drops the ingestor pods out of your local cluster smoothly

```

### 5. Reset Workspace Assets

Strip local code coverage caches, compiled JavaScript outputs, local hidden Terraform provider modules, and running cluster deployment resources simultaneously to restore a pristine directory state:

```bash
make clean

```

---

## ⚙️ Automated Quality Gates (CI/CD)

Any pull request or push code modification targeted at the `main` branch triggers the automated verification pipeline inside `.github/workflows/ci-cd.yml`. The runner guarantees a high stability baseline by enforcing:

1. **Dependency Alignment:** Verifies and locks sub-workspace trees cleanly.
2. **Software Verification:** Re-runs Jest unit validations across all applications to shield against regression bugs.
3. **IaC Linting:** Audits Terraform configuration patterns via `terraform fmt`.
4. **Architectural Compliance:** Natively evaluates structural cloud logic via `terraform test` to ensure infrastructure schemas strictly match cloud provider requirements before allowing continuous delivery state promotions.

```

```