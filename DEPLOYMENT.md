# Deploying NexShare (Coolify)

Two Coolify "Resources" — one per app, each built from its own `Dockerfile`
— plus a Postgres and a Redis resource. Both Dockerfiles are verified
locally (`docker build` + `docker run`, wired together, a real
registration call through the full stack) — see the commit this file
shipped in.

## 1. Provision the database first

In Coolify: **New Resource → Database → PostgreSQL**, and separately
**New Resource → Database → Redis**. Note the internal connection string
each one gives you (something like `postgres-xxxx:5432` /
`redis-xxxx:6379` — Coolify resources reach each other by service name on
its internal network, not by the host's public IP).

## 2. Deploy the API

**New Resource → your Git repo → set the base directory to `apps/api`**
so Coolify finds `apps/api/Dockerfile`.

Environment variables (see `apps/api/.env.example` for the full
reference/defaults — these are the ones that **must** change for
production, not stay at their dev default):

| Variable | Set to |
|---|---|
| `DATABASE_URL` | `postgresql+psycopg://<user>:<pass>@<postgres-service>:5432/<db>` — from step 1 |
| `REDIS_URL` | `redis://<redis-service>:6379/0` — from step 1 |
| `JWT_SECRET` | a real random 32+ byte secret — **never** the committed dev default |
| `ENVIRONMENT` | `production` (makes the session cookie `Secure`) |
| `CORS_ORIGINS` | `["https://<your-web-domain>"]` |
| `PUBLIC_BASE_URL` | `https://<your-web-domain>` (used to build shareable tracking-link URLs) |
| `PAYSTACK_SECRET_KEY` | your live or test key, if payouts should work |
| `RESEND_API_KEY` / `TERMII_API_KEY` | set both if you want real email/SMS delivery — otherwise OTP codes just land in this resource's container logs (see §4) |

Migrations run automatically on every container start
(`docker-entrypoint.sh` runs `alembic upgrade head` before starting
uvicorn) — nothing extra to trigger by hand on deploy.

**Uploads are not persistent by default.** Business-uploaded offer images
go to `apps/api/uploads/` inside the container (`app/main.py` mounts it at
`/uploads`), which is lost on every redeploy unless you attach a Coolify
persistent volume mounted at `/app/uploads` on this resource.

Set a domain for this resource once it's deployed (e.g.
`api.yourdomain.com`) — you'll need its address for step 3.

## 3. Deploy the web app

**New Resource → same Git repo → base directory `apps/web`.**

This one needs a **build argument**, not a runtime env var:

| Build Arg | Set to |
|---|---|
| `API_URL` | the API resource's address from step 2 (its Coolify-internal service address if they're meant to talk over the internal network, or its public domain if not — either works, but prefer internal) |

This is not a mistake to skip past: Next.js evaluates `next.config.js`'s
`rewrites()` (which reads `API_URL`) once, at `next build` — a
runtime/environment-variable override set after the image is built has
**no effect**. Confirmed directly: the proxy silently failed
(`ECONNREFUSED 127.0.0.1:8000`, the compiled-in default) until `API_URL`
was supplied as a build arg instead. If you ever need to point this app at
a different API address, that requires a rebuild, not just a redeploy with
a changed env var.

Set a public domain for this resource too (e.g. `app.yourdomain.com`) —
that's the URL you'll actually share with users, and what you should feed
back into the API resource's `CORS_ORIGINS` / `PUBLIC_BASE_URL` in step 2.

## 4. First login after deploy

Without `RESEND_API_KEY`/`TERMII_API_KEY` set, verification codes aren't
emailed or texted. The verification screen shows them directly instead, in
a labeled amber "TEST MODE" banner — no need to dig through the API
resource's Coolify logs. This is self-disabling: once both keys are set on
the API resource and it redeploys, the banner and codes stop appearing on
their own.

## Verified locally before this was written

- `docker build` succeeds for both `apps/api/Dockerfile` and
  `apps/web/Dockerfile`.
- The API container runs real Alembic migrations against a fresh Postgres
  and serves real requests (`/health`, `/docs`, a real `401` from
  `/api/auth/login`).
- The web container's `/api/*` proxy correctly reaches the API container
  over a Docker network — once `API_URL` was passed as a build arg,
  confirmed by a real `POST /api/auth/register` through the full stack
  (frontend container → backend container → real Postgres row → real
  Redis-backed OTP code in the backend's logs).

## Not yet done

- Nothing in this repo has been deployed to a live Coolify instance —
  this document and the two Dockerfiles are the prerequisite, not a
  record of an actual deployment. The dashboard clicks (New Resource,
  env vars, Deploy) themselves still need to happen.
- No CI step builds or pushes these images yet — `.github/workflows/ci.yml`
  only runs tests/lint/build-check, it doesn't publish a Docker image.
  Coolify builds the image itself from the Dockerfile on each deploy, so
  this isn't blocking, just worth knowing if you later want a faster
  deploy or an image registry in the loop.
