# --- Build Stage ---
FROM node:20-alpine AS builder
WORKDIR /usr/src/app

# Copy monorepo root configurations
COPY package*.json tsconfig.base.json ./
# Copy workspace targets
COPY packages/event-schemas ./packages/event-schemas
COPY apps/processor-storage ./apps/processor-storage

# Install dependencies and build typescript
RUN npm ci
RUN npm run build --workspace=apps/processor-storage

# --- Production Runtime Stage ---
FROM node:20-alpine AS runner
WORKDIR /usr/src/app
ENV NODE_ENV=production

COPY package*.json ./
COPY --from=builder /usr/src/app/packages/event-schemas ./packages/event-schemas
COPY --from=builder /usr/src/app/apps/processor-storage/dist ./apps/processor-storage/dist
COPY --from=builder /usr/src/app/apps/processor-storage/package.json ./apps/processor-storage/package.json

# Install production-only dependencies across workspaces
RUN npm ci --omit=dev

CMD ["node", "apps/processor-storage/dist/index.js"]