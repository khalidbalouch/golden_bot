FROM python:3.10-slim-bullseye
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl gnupg && apt-get clean && rm -rf /var/lib/apt/lists/*
ARG UID=1000; ARG GID=1000
RUN groupadd -g $GID botuser && useradd -u $UID -g botuser -m -s /bin/bash botuser
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt
COPY --chown=botuser:botuser core/ ./core/
COPY --chown=botuser:botuser tests/ ./tests/
COPY --chown=botuser:botuser main.py .
RUN mkdir -p /app/logs /app/data && chown -R botuser:botuser /app
USER botuser
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 CMD python -c "import sys; sys.exit(0)" || exit 1
EXPOSE 8080
CMD ["python", "-m", "main"]
