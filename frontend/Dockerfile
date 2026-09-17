# Multi-stage production container for FFIRE Frontend UI (Chapter 60)
FROM node:20-alpine as builder

WORKDIR /app

# Copy package descriptors
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy application source
COPY . .

# Build production bundle
RUN npm run build

# Serve stage with minimal Nginx Alpine
FROM nginx:alpine as runner

WORKDIR /usr/share/nginx/html

# Remove default static files
RUN rm -rf ./*

# Copy built assets from builder stage
COPY --from=builder /app/dist .

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD wget -q --spider http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
