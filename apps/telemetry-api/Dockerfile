# Stage 1: Build and Compilations
FROM node:20-alpine AS builder
WORKDIR /usr/src/app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: Hardened Minimal Production Execution Environment
FROM node:20-alpine AS runner
WORKDIR /usr/src/app
ENV NODE_ENV=production

COPY package*.json ./
RUN npm ci --only=production

# Pull only the compiled JS from the builder stage
COPY --from=builder /usr/src/app/dist ./dist

# Security: Revoke default root context privileges
USER node

EXPOSE 3000
CMD ["node", "dist/app.js"]