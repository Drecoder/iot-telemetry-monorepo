.PHONY: all help install test test-app test-infra security-scan coverage dev-build dev-load dev-deploy dev-clean clean

# --- CONSTANTS & CONFIGURATION ---
IMAGE_NAME := telemetry-ingestor:dev

# Default target runs everything from code quality check to local cluster deployment
all: test dev-build dev-load dev-deploy

help:
	@echo "========================================================================"
	@echo "            IoT FLEET TELEMETRY MONOREPO INTEGRATED TOOLCHAIN           "
	@echo "========================================================================"
	@echo "Verification Commands:"
	@echo "  make install        - Install all monorepo dependencies cleanly"
	@echo "  make test           - Run application, infrastructure, and security suites"
	@echo "  make test-app       - Run application unit tests via Jest"
	@echo "  make test-infra     - Run native Terraform configuration tests"
	@echo "  make security-scan  - Execute Checkov Static Infrastructure Security Scan"
	@echo "  make coverage       - Run application tests and output HTML coverage reports"
	@echo "------------------------------------------------------------------------"
	@echo "Local Minikube Deployment Commands (WSL Native):"
	@echo "  make all            - Run entire validation pipeline, then build & deploy"
	@echo "  make dev-build      - Build the telemetry-ingestor image in WSL"
	@echo "  make dev-load       - Inject the built image directly into Minikube"
	@echo "  make dev-deploy     - Apply production-agnostic manifest to Minikube"
	@echo "  make dev-clean      - Strip deployment out of the local cluster"
	@echo "  make clean          - Strip local build artifacts, logs, and coverage"
	@echo "========================================================================"

# --- VERIFICATION & VALIDATION GATEWAY ---

install:
	npm ci

test: test-app test-infra security-scan

test-app:
	npm test --workspaces --if-present

test-infra:
	terraform -chdir=infra/terraform init -backend=false
	terraform -chdir=infra/terraform validate
	terraform -chdir=infra/terraform test

security-scan:
	@echo "========================================================================"
	@echo "   RUNNING CHECOV STATIC INFRASTRUCTURE SECURITY ANALYZER                "
	@echo "========================================================================"
	docker run --rm -v $(PWD)/infra/terraform:/tf bridgecrew/checkov:latest -d /tf --framework terraform --quiet

coverage:
	npx jest --projects apps/telemetry-api --coverage --coverageDirectory=../../coverage


# --- LOCAL MINIKUBE KUBERNETES DEPLOYMENT LAYER ---

dev-build:
	@echo "🔨 Building telemetry-ingestor image inside WSL..."
	docker build --no-cache -t $(IMAGE_NAME) -f apps/telemetry-api/Dockerfile .

dev-load:
	@echo "🔍 Validating Minikube profile availability..."
	@minikube status >/dev/null 2>&1 || (echo "🚀 Minikube cluster stopped or profile missing. Auto-booting driver..." && minikube start --driver=docker)
	@echo "🚚 Loading image layer cache directly into Minikube container runtime..."
	minikube image load $(IMAGE_NAME) --overwrite

dev-deploy:
	@echo "🔍 Validating Minikube control-plane state before deployment..."
	@minikube status >/dev/null 2>&1 || (echo "🚀 Minikube cluster stopped or profile missing. Auto-booting driver..." && minikube start --driver=docker)
	@echo "🧹 Purging historical pod states to clean up conflicting ReplicaSets..."
	-minikube kubectl -- delete deployment telemetry-ingestor --ignore-not-found=true
	@echo "🚀 Applying environment-agnostic deployment manifest..."
	minikube kubectl -- apply -f infra/k8s/telemetry-ingestor.yaml
	@echo "🔄 Verifying rollout status (waiting for index.ts bootstrap listener)..."
	-minikube kubectl -- rollout status deployment/telemetry-ingestor --timeout=60s
	@echo "📊 Finalizing pod initialization status:"
	minikube kubectl -- get pods

dev-clean:
	@echo "🧹 Removing telemetry-ingestor deployment from cluster..."
	-minikube kubectl -- delete -f infra/k8s/telemetry-ingestor.yaml


# --- CLEANUP LAYER ---

clean: dev-clean
	@echo "🧹 Stripping local build artifacts and coverage reports..."
	rm -rf coverage
	rm -rf apps/telemetry-api/dist
	rm -rf infra/terraform/.terraform
	rm -rf infra/terraform/.terraform.lock.hcl