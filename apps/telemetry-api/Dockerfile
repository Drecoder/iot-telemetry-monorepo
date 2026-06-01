# Stage 1: Build and Compilations
FROM node:20-alpine AS builder
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
FROM node:20-alpine AS runner
WORKDIR /usr/src/app
ENV NODE_ENV=production

# Copy root package configurations and entire monorepo workspace maps
COPY package*.json ./
COPY apps/telemetry-api/package*.json ./apps/telemetry-api/
COPY packages/shared-types/package*.json ./packages/shared-types/
COPY packages/event-schemas/package*.json ./packages/event-schemas/

# Install production dependencies strictly optimizing for the workspace layout
# Note: npm 10+ prefers --omit=dev over --only=production, but both are valid
RUN npm ci --omit=dev --workspace=telemetry-api

# 🚀 FIX 1: Pull the compiled JS preserving its TRUE workspace directory path
COPY --from=builder /usr/src/app/apps/telemetry-api/dist ./apps/telemetry-api/dist

# Security: Revoke default root context privileges
USER node

EXPOSE 3000

# 🚀 FIX 2: Execute the entrypoint pointing to the actual nested application target
CMD ["node", "apps/telemetry-api/dist/index.js"]