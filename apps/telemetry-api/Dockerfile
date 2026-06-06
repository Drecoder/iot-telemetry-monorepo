# Stage 1: Build and Compilations
# FIXED: Pinned base image to an immutable, secure version to resolve CKV_DOCKER_7
FROM node:24.1.0-alpine3.19 AS builder
WORKDIR /usr/src/app

# 1. Copy ALL workspace manifests and base configs to establish the dependency graph
COPY package*.json tsconfig*.json ./
COPY apps/telemetry-api/package*.json ./apps/telemetry-api/
COPY packages/shared-types/package*.json ./packages/shared-types/
COPY packages/event-schemas/package*.json ./packages/event-schemas/

# 2. Install dependencies for the entire monorepo layout
RUN npm ci

# 3. Copy the remaining source files into the container
COPY . .

# 4. Compile the specific sub-workspace
RUN npm run build --workspace=telemetry-api

# Stage 2: Hardened Minimal Production Execution Environment
# FIXED: Pinned runtime stage to match the builder security profile
FROM node:24.1.0-alpine3.19 AS runner
WORKDIR /usr/src/app
ENV NODE_ENV=production

# Copy root package configurations and entire monorepo workspace maps
COPY package*.json ./
COPY apps/telemetry-api/package*.json ./apps/telemetry-api/
COPY packages/shared-types/package*.json ./packages/shared-types/
COPY packages/event-schemas/package*.json ./packages/event-schemas/

# FIXED: Consolidated production installation and directory ownership adjustments into a single layer.
# This prevents permission errors and avoids consecutive layer bloating.
RUN npm ci --omit=dev --workspace=telemetry-api && \
    chown -R node:node /usr/src/app

# 🚀 FIX 1: Pull the compiled JS preserving its TRUE workspace directory path
# Explicitly assign ownership to the non-root user during file extraction
COPY --from=builder --chown=node:node /usr/src/app/apps/telemetry-api/dist ./apps/telemetry-api/dist

# Security: Revoke default root context privileges
# FIXED: Verified non-root context execution to fully clear CKV_DOCKER_3 and CKV_DOCKER_8
USER node

EXPOSE 3000

# 🚀 FIX 2: Execute the entrypoint pointing to the actual nested application target
CMD ["node", "apps/telemetry-api/dist/index.js"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1