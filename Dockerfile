FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
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

# Copy requirements first for better caching
COPY production_requirements.txt requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip cache purge && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs reports data temp

# Apply SEO meta tags to Streamlit template (before switching to non-root user)
RUN python utils/apply_seo_template.py

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

# Create Streamlit config matching production settings
RUN mkdir -p ~/.streamlit && \
    printf '[server]\n\
headless = true\n\
address = "0.0.0.0"\n\
port = 5000\n\
enableCORS = false\n\
enableXsrfProtection = false\n\
maxUploadSize = 1000\n\
enableStaticServing = true\n\
fileWatcherType = "none"\n\
\n\
[browser]\n\
gatherUsageStats = false\n\
serverAddress = "dataguardianpro.nl"\n\
serverPort = 443\n\
\n\
[theme]\n\
primaryColor = "#4267B2"\n\
backgroundColor = "#FFFFFF"\n\
secondaryBackgroundColor = "#F0F2F5"\n\
textColor = "#1E293B"\n\
font = "sans serif"\n\
\n\
[global]\n\
developmentMode = false\n\
showWarningOnDirectExecution = false\n\
\n\
[logger]\n\
level = "warning"\n\
\n\
[runner]\n\
fastReruns = true\n\
magicEnabled = true\n\
\n\
[client]\n\
showErrorDetails = false\n\
toolbarMode = "minimal"\n\
showSidebarNavigation = false\n' > ~/.streamlit/config.toml

# Expose ports
EXPOSE 5000 5001

# Smart healthcheck: detects whether this is the main app (port 5000) or webhook server (port 5001)
HEALTHCHECK --interval=30s --timeout=30s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5000/_stcore/health 2>/dev/null || curl -f http://localhost:5001/health 2>/dev/null || exit 1

# Run application on port 5000
CMD ["streamlit", "run", "app.py", "--server.port", "5000", "--server.address", "0.0.0.0", "--server.headless", "true"]
