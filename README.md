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

A root-level `Makefile` simplifies local developer operations (DX). Ensure you have Node.js (v20+), Docker, and Terraform (v1.5+) installed locally.

### 1. Initialize Project & Workspaces

Install all node module dependencies cleanly across every internal npm workspace:

```bash
make install

```

### 2. Execute Full Test Suite

Trigger both the software unit testing engine (Jest) and the native cloud infrastructure test validations simultaneously to run a full local verification pass:

```bash
make test

```

### 3. Run Application Tests & Mocking

Run the TypeScript API and worker testing layer independently. This suite isolates business logic from live cloud environments by natively mocking AWS SDK client interactions and capturing structured logger streams via error-state behavior tracking:

```bash
make test-app

```

### 4. Run Cloud Infrastructure Assertions

Validate syntax correctness, check resource compliance, and execute native `.tftest.hcl` plan assertions to verify resource properties (such as valid On-Demand Kinesis stream mode configurations) without spinning up live hardware:

```bash
make test-infra

```

### 5. Generate Test Coverage Report

Generate comprehensive metrics mapping your application code execution coverage. This project targets a highly stable baseline, maintaining >95% statement coverage across application entrypoints:

```bash
make coverage

```

*This outputs a summary directly to the terminal and builds a visual HTML dashboard located locally at `coverage/lcov-report/index.html`.*

### 6. Clean Up Workspace

Strip build artifacts, local coverage caches, and compiled JS files out of your workspace directories:

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