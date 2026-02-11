FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libpq-dev \
    postgresql-client \
    tesseract-ocr \
    libxml2-dev \
    libxmlsec1-dev \
    libxmlsec1-openssl \
    && rm -rf /var/lib/apt/lists/*

COPY production_requirements.txt requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p logs reports data temp

RUN python utils/apply_seo_template.py

ENV ENVIRONMENT=production
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN useradd --create-home --shell /bin/bash dataguardian && \
    chown -R dataguardian:dataguardian /app
USER dataguardian

RUN mkdir -p ~/.streamlit && \
    cp /app/.streamlit/config.toml ~/.streamlit/config.toml

EXPOSE 5000 5001

HEALTHCHECK --interval=30s --timeout=30s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5000/_stcore/health 2>/dev/null || curl -f http://localhost:5001/health 2>/dev/null || exit 1

CMD ["streamlit", "run", "app.py", "--server.port", "5000", "--server.address", "0.0.0.0", "--server.headless", "true"]
