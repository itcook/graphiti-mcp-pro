# syntax=docker/dockerfile:1.9
# Multi-stage build for React frontend

# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package.json pnpm-lock.yaml ./

# Install pnpm
RUN npm install -g pnpm

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy source code
COPY . ./

# Set build arguments from docker-compose args
ARG VITE_MCP_PORT
ARG VITE_MANAGER_SERVER_PORT
ARG VITE_MANAGER_SERVER_HOST
ARG VITE_API_BASE_URL

# Build the application
RUN pnpm run build

# Production stage
FROM caddy:alpine

# Copy built files from builder stage
COPY --from=builder /app/dist /usr/share/frontend

# Copy Caddyfile
COPY ./Caddyfile /etc/caddy/Caddyfile

# Expose port
EXPOSE 80

# Start caddy
CMD ["caddy", "run", "--config", "/etc/caddy/Caddyfile"]