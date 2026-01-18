FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including pycairo via apt
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libpq-dev \
    postgresql-client \
    tesseract-ocr \
    pkg-config \
    libcairo2-dev \
    libgirepository1.0-dev \
    libffi-dev \
    libpango1.0-dev \
    libgdk-pixbuf2.0-dev \
    libxml2-dev \
    libxmlsec1-dev \
    libxmlsec1-openssl \
    python3-cairo \
    cmake \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY production_requirements.txt requirements.txt

# Install pycairo with pre-built wheel, then rest of dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir "pycairo==1.26.0" && \
    pip install --no-cache-dir -r requirements.txt && \
    pip cache purge && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs reports data temp

# Set production environment variables
ENV ENVIRONMENT=production
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_PORT=5000
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Create user for security
RUN useradd --create-home --shell /bin/bash dataguardian && \
    chown -R dataguardian:dataguardian /app
USER dataguardian

# Create Streamlit config
RUN mkdir -p ~/.streamlit && \
    echo '[server]\n\
headless = true\n\
address = "0.0.0.0"\n\
port = 5000\n\
enableCORS = false\n\
enableXsrfProtection = false\n\
\n\
[browser]\n\
gatherUsageStats = false\n\
\n\
[theme]\n\
base = "light"' > ~/.streamlit/config.toml

# Expose port 5000 for production
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/_stcore/health || exit 1

# Run application on port 5000
CMD ["streamlit", "run", "app.py", "--server.port", "5000", "--server.address", "0.0.0.0", "--server.headless", "true"]