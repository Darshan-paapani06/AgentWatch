# Stage 1: Build optimization and dependency caching
FROM node:20-alpine AS builder
WORKDIR /app

# Required system dependency for certain native node modules
RUN apk add --no-cache libc6-compat

# Cache dependencies unless package metadata changes
COPY package*.json ./
RUN npm ci

# Copy app sources after installing deps
COPY . .

# Set up build-time arguments securely
ARG NEXT_PUBLIC_API_HOST
ARG NEXT_PUBLIC_WS_URL

# Expose arguments to the build process environment safely
ENV NEXT_PUBLIC_API_HOST=$NEXT_PUBLIC_API_HOST \
    NEXT_PUBLIC_WS_URL=$NEXT_PUBLIC_WS_URL \
    NEXT_TELEMETRY_DISABLED=1

RUN npm run build

# Stage 2: Clean, unprivileged runtime environment
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

# Create application system user to safely execute without root access
RUN addgroup --system --gid 1001 nodejs \
 && adduser --system --uid 1001 nextjs

# Pull compiled standalone assets with proper owner permissions
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/public ./public

USER nextjs
EXPOSE 3000

# Execute next.js standalone platform server
CMD ["node", "server.js"]
