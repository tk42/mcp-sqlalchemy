FROM python:3.12-slim

WORKDIR /app

COPY mcp-alchemy /app/mcp-alchemy

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    python3-pip \
    gnupg2 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Add Microsoft repository and install ODBC driver
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && apt-get remove --purge -y unixodbc unixodbc-dev \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends \
    msodbcsql18 \
    unixodbc \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN pip install uv

# Create virtual environment
RUN uv venv

# Create directories for package cache
RUN mkdir -p /app/.cache/pip
RUN mkdir -p /app/.cache/uv

# Copy dependency files
COPY pyproject.toml .
COPY README.md .

# Install hatchling first
RUN . .venv/bin/activate && uv pip install --cache-dir=/app/.cache/pip hatchling

# Download and cache dependencies
RUN . .venv/bin/activate
RUN uv sync --all-packages --cache-dir=/app/.cache/pip

WORKDIR /app/mcp-alchemy
RUN uv sync --all-packages --cache-dir=/app/.cache/pip

WORKDIR /app

# Copy application files
COPY app.py .
COPY utils ./utils

# Expose port for Streamlit
EXPOSE 8501

# Set PATH to include the virtual environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PIP_NO_INDEX=true
ENV PIP_FIND_LINKS="/app/.cache/pip"

# Run the Streamlit application
CMD ["streamlit", "run", "app.py"]
