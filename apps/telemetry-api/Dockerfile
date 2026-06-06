# Stage 1: Build and Compilations
# FIXED: Replaced invalid minor version string with the official registry tag format
FROM node:24-alpine3.19 AS builder
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
# FIXED: Aligned the production image tag with the verified upstream variant
FROM node:24-alpine3.19 AS runner
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

# Explicitly assign ownership to the non-root user during file extraction
COPY --from=builder --chown=node:node /usr/src/app/apps/telemetry-api/dist ./apps/telemetry-api/dist

# Security: Revoke default root context privileges
USER node

EXPOSE 3000


# external packages, keeping your production attack surface minimal.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD node -e "const req = require('http').request('http://localhost:3000/health', { timeout: 2000 }, (res) => { process.exit(res.statusCode === 200 ? 0 : 1); }); req.on('error', () => process.exit(1)); req.end();"

CMD ["node", "apps/telemetry-api/dist/index.js"]