FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORTAL_ENV=production \
    PORTAL_DATABASE=/data/portal.db

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --system --uid 10001 --user-group --create-home portal

COPY --chown=portal:portal . .
RUN mkdir -p /data && chown portal:portal /data

LABEL org.opencontainers.image.source="https://github.com/polamanasa03/hr_portal"

USER portal
EXPOSE 5000

CMD ["sh", "-c", "exec gunicorn --bind=0.0.0.0:${PORT:-5000} --workers=2 --access-logfile=- --error-logfile=- app:app"]
