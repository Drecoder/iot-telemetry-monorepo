
```markdown
# IoT Fleet Telemetry Monorepo

A production-ready, full-stack cloud monorepo designed to ingest, validate, and persist high-volume, real-time time-series telemetry data from a globally distributed fleet of 20,000 concurrent autonomous robots.

This project implements a unified architecture combining **Cloud Platform Engineering (Infrastructure as Code, Hardened Containers, CI/CD)** with **Software Engineering (TypeScript, Node.js, Express)** under a single, cohesive source of truth.

## 🏗️ Architectural Overview

The system handles streaming edge data by decoupling the ingress layer from the persistence layer to maintain low latencies and high availability:

* **Ingress Layer:** An AWS Application Load Balancer (ALB) or API Gateway handles SSL/TLS termination and routes traffic securely.
* **Compute Layer:** A high-throughput TypeScript/Node.js REST API packaged in minimalist, non-root multi-stage Docker containers (`node:20-alpine`). Orchestrated via AWS EKS (Kubernetes) or ECS Fargate in isolated private subnets.
* **Persistence Layer:** Amazon DynamoDB serves as the time-series datastore, utilizing a distributed partition key (`robotId`) and chronological sort key (`timestamp`) to handle massive concurrent writes.
* **Infrastructure as Code (IaC):** Explicit cloud topologies and guardrails declared completely using modular Terraform.

---

## 📂 Repository Structure

The monorepo uses standard workspaces to keep applications, packages, and operational layers strictly separated yet perfectly synchronized:

```text
cnh-telemetry-monorepo/
├── .github/workflows/
│   └── ci-cd.yml          # GitHub Actions CI/CD automation pipeline
├── apps/
│   └── telemetry-api/     # TypeScript Ingestion Microservice & Dockerfile
├── infra/
│   └── terraform/         # Declarative AWS Blueprints (VPC, ECS, DynamoDB)
│       └── tests/         # Native HCL infrastructure plan assertions
├── packages/
│   └── shared-types/      # Centralized invariant data contracts and schemas
├── Makefile               # Local development task runner orchestrator
├── package.json           # Root npm workspaces definition
└── tsconfig.base.json     # Global shared TypeScript configuration rules

```

---

## 🚀 Local Development & Toolchain

A root-level `Makefile` is provided to simplify local developer operations (DX). Ensure you have Node.js (v20+), Docker, and Terraform (v1.5+) installed locally.

### 1. Initialize Project & Workspaces

Install all node module dependencies cleanly across every internal workspace:

```bash
make install

```

### 2. Execute Full Test Suite

Trigger both the software unit testing engine (Jest) and the native cloud infrastructure test validations simultaneously:

```bash
make test

```

### 3. Run Application Tests & Mocking

Run the TypeScript API testing layer independently. This suite isolates code logic from live cloud environments by natively mocking AWS SDK database interactions:

```bash
make test-app

```

### 4. Run Cloud Infrastructure Assertions

Validate syntax correctness, check resource compliance, and execute native `.tftest.hcl` plan assertions without spinning up live hardware:

```bash
make test-infra

```

### 5. Generate Test Coverage Report

Generate comprehensive metrics mapping your code execution coverage:

```bash
make coverage

```

*This outputs a summary directly to the terminal and builds a visual HTML dashboard located locally at `coverage/lcov-report/index.html`.*

### 6. Clean Up Workspace

Strip build artifacts, local caches, and compiled JS files out of your workspace directories:

```bash
make clean

```

---

## ⚙️ Automated Quality Gates (CI/CD)

Any pull request or push code modification targeted at the `main` branch triggers the automated verification pipeline inside `.github/workflows/ci-cd.yml`. The runner guarantees a high stability baseline by enforcing:

1. **Dependency Alignment:** Verifies and locks sub-workspace trees cleanly.
2. **Software Verification:** Re-runs Jest unit validations to shield against regression errors.
3. **IaC Linting:** Audits configuration patterns via `terraform fmt`.
4. **Architectural Compliance:** Validates structural cloud logic via `terraform test` before allowing infrastructure state promotions.

```
---

### 💡 Why this README wraps up your tech presentation perfectly:
* **Highlights DX Mindset:** Demonstrating that you treat local developer loops with the same importance as production pipelines instantly communicates senior-level leadership and maturity.
* **Clear Operational Playbook:** Anyone on the panel can check out this repository, look at the markdown, type `make test`, and see the entire system compile and self-verify smoothly.

```# iot-telemetry-monorepo
# iot-telemetry-monorepo
