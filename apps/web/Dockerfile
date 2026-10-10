# Production image for the Next.js frontend, built as a standalone server
# (see next.config.js `output: "standalone"`) so the final image ships only
# the traced dependency subset, not the full node_modules tree.

FROM node:20-slim AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:20-slim AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# Next.js evaluates next.config.js's rewrites() — including this
# process.env.API_URL read — once at `next build`, not per-request or at
# container start. A docker run -e API_URL=... has no effect after the
# image is built; it must be supplied here, as a build arg, instead.
ARG API_URL
ENV API_URL=${API_URL}
RUN npm run build

FROM node:20-slim AS runner
WORKDIR /app
ENV NODE_ENV=production
# The standalone server binds to this host:port — HOSTNAME defaults to
# localhost otherwise, which is unreachable from outside the container.
ENV HOSTNAME=0.0.0.0
ENV PORT=3000

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000
CMD ["node", "server.js"]
