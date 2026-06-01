# Stage 1: Build and Compilations
FROM node:20-alpine AS builder
WORKDIR /usr/src/app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build --workspace=telemetry-api -- --ignoreDeprecations 6.0

# Stage 2: Hardened Minimal Production Execution Environment
FROM node:20-alpine AS runner
WORKDIR /usr/src/app
ENV NODE_ENV=production

# Copy root package configurations and entire monorepo workspace maps
COPY package*.json ./
COPY apps/telemetry-api/package*.json ./apps/telemetry-api/
COPY packages/shared-types/package*.json ./packages/shared-types/

# Install production dependencies strictly optimizing for the workspace layout
RUN npm ci --only=production --workspace=telemetry-api

# Pull only the compiled JS from the builder stage
COPY --from=builder /usr/src/app/apps/telemetry-api/dist ./dist

# Security: Revoke default root context privileges
USER node

EXPOSE 3000
CMD ["node", "dist/app.js"]