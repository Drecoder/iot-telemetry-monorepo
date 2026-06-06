# Stage 1: Build and Compilations
# FIXED: Updated to a verified, official Node 24 Alpine image tag structure
FROM node:24-alpine AS builder
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
# FIXED: Aligned the production image tag with the verified runtime variant
FROM node:24-alpine AS runner
WORKDIR /usr/src/app
ENV NODE_ENV=production

# Copy root package configurations and entire monorepo workspace maps
COPY package*.json ./
COPY apps/telemetry-api/package*.json ./apps/telemetry-api/
COPY packages/shared-types/package*.json ./packages/shared-types/
COPY packages/event-schemas/package*.json ./packages/event-schemas/

# FIXED: Consolidated production installation and directory ownership adjustments into a single layer
RUN npm ci --omit=dev --workspace=telemetry-api && \
    chown -R node:node /usr/src/app

# 🚀 FIX 1: Pull the compiled JS preserving its TRUE workspace directory path
# Explicitly assign ownership to the non-root user during file extraction
COPY --from=builder --chown=node:node /usr/src/app/apps/telemetry-api/dist ./apps/telemetry-api/dist

# Security: Revoke default root context privileges
# FIXED: Verified non-root context execution to fully clear CKV_DOCKER_3 and CKV_DOCKER_8
USER node

EXPOSE 3000

# FIXED: Native healthcheck using Node's HTTP module to eliminate external binary dependencies
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD node -e "const req = require('http').request('http://localhost:3000/health', { timeout: 2000 }, (res) => { process.exit(res.statusCode === 200 ? 0 : 1); }); req.on('error', () => process.exit(1)); req.end();"

# 🚀 FIX 2: Execute the entrypoint pointing to the actual nested application target
CMD ["node", "apps/telemetry-api/dist/index.js"]