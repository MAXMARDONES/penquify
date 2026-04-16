FROM python:3.12-slim

WORKDIR /app

# System deps for Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libatk-bridge2.0-0 libdrm2 libxcomposite1 libxdamage1 \
    libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2 libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md LICENSE ./
COPY penquify/ penquify/

RUN pip install --no-cache-dir ".[api]" && playwright install --with-deps chromium

EXPOSE 8080

CMD ["uvicorn", "penquify.api.server:app", "--host", "0.0.0.0", "--port", "8080"]
