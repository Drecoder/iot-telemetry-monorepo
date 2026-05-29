.PHONY: help install test test-app test-infra coverage clean

# Default target when someone just types 'make'
help:
	@echo "========================================================================"
	@echo "                IoT FLEET TELEMETRY MONOREPO TOOLCHAIN                  "
	@echo "========================================================================"
	@echo "Available commands:"
	@echo "  make install      - Install all monorepo dependencies cleanly"
	@echo "  make test         - Run both application and infrastructure test suites"
	@echo "  make test-app     - Run application unit tests via Jest"
	@echo "  make test-infra   - Run native Terraform configuration tests"
	@echo "  make coverage     - Run application tests and output HTML coverage reports"
	@echo "  make clean        - Strip build artifacts, coverage reports, and node_modules"
	@echo "========================================================================"

# Install dependencies across all npm workspaces
install:
	npm ci

# Orchestrate both test pipelines sequentially
test: test-app test-infra

# Execute TypeScript API unit tests inside workspaces
test-app:
	npm test --workspaces --if-present

# Initialize and execute native Terraform structural plan assertions
test-infra:
	terraform -chdir=infra/terraform init -backend=false
	terraform -chdir=infra/terraform validate
	terraform -chdir=infra/terraform test

# Execute test metrics and generate coverage output
coverage:
	npx jest --projects apps/telemetry-api --coverage --coverageDirectory=../../coverage

# Clean up temporary generation assets
clean:
	rm -rf coverage
	rm -rf apps/telemetry-api/dist
	rm -rf infra/terraform/.terraform
	rm -rf infra/terraform/.terraform.lock.hcl