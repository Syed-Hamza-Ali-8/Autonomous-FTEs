# Tollgate web app (Phase 7): the Next.js store and staff console, built for production.
# NEXT_PUBLIC_* values are inlined at build time, so they are build arguments. The anon key is public by design
# (sign-in only); the service-role key never reaches the frontend (invariant 21).
#
# Packages are downloaded ONCE (stage deps). The runtime stage copies them and drops the dev ones, rather than
# running a second `npm ci`: two parallel installs inside Docker Desktop reset the network connection after 21
# minutes on the first build (2026-11-14). The npm cache mount lets a retried build reuse what was downloaded.
FROM node:24.22.2-bookworm-slim AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci --fetch-retries=5 --fetch-retry-mintimeout=20000 --fetch-retry-maxtimeout=120000

FROM deps AS build
COPY . .
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_SUPABASE_URL
ARG NEXT_PUBLIC_SUPABASE_ANON_KEY
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL \
    NEXT_PUBLIC_SUPABASE_URL=$NEXT_PUBLIC_SUPABASE_URL \
    NEXT_PUBLIC_SUPABASE_ANON_KEY=$NEXT_PUBLIC_SUPABASE_ANON_KEY \
    NEXT_TELEMETRY_DISABLED=1
RUN npm run build && npm prune --omit=dev

FROM node:24.22.2-bookworm-slim
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1
COPY --from=build /app/package.json ./package.json
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/.next ./.next
COPY --from=build /app/next.config.ts ./next.config.ts
EXPOSE 3000
CMD ["npx", "next", "start", "--port", "3000"]
