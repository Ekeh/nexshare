# Production image for the FastAPI backend. Runs migrations on container
# start (see docker-entrypoint.sh) then serves with uvicorn — no --reload,
# that's a dev-only flag (apps/api/app/main.py is the ASGI app either way).
FROM python:3.12-slim

WORKDIR /app

# psycopg[binary] and bcrypt ship prebuilt wheels for this base image, so no
# compiler toolchain is needed here — keep the image lean.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY alembic.ini .
COPY alembic ./alembic
COPY app ./app
COPY docker-entrypoint.sh .
RUN chmod +x docker-entrypoint.sh && mkdir -p uploads

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
