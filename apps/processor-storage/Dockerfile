# --- Build Stage ---
# Pinned to a deterministic Node 24 variant to align with your pipeline's updated environment
FROM node:24.1.0-alpine3.19 AS builder
WORKDIR /usr/src/app

# Copy monorepo root configurations for dependency resolution
COPY package*.json tsconfig.base.json ./
# Copy shared workspace packages and the target application
COPY packages/event-schemas ./packages/event-schemas
COPY apps/processor-storage ./apps/processor-storage

# FIXED: Consolidated consecutive RUN instructions into a single layer to resolve DL3059
RUN npm ci && \
    npm run build --workspace=apps/processor-storage

# --- Production Runtime Stage ---
FROM node:24.1.0-alpine3.19 AS runner
WORKDIR /usr/src/app
ENV NODE_ENV=production

COPY package*.json ./
COPY --from=builder /usr/src/app/packages/event-schemas ./packages/event-schemas
COPY --from=builder /usr/src/app/apps/processor-storage/dist ./apps/processor-storage/dist
COPY --from=builder /usr/src/app/apps/processor-storage/package.json ./apps/processor-storage/package.json

# FIXED: Consolidated production installation and dropped root privileges in the same phase
# Enforces an explicit low-privilege USER context to eliminate runtime container escapes
RUN npm ci --omit=dev && \
    chown -R node:node /usr/src/app

USER node

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1

CMD ["node", "apps/processor-storage/dist/index.js"]