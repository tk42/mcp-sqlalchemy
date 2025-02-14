FROM python:3.12-slim

WORKDIR /app

COPY mcp-alchemy ./mcp-alchemy

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

# Expose port for Streamlit
EXPOSE 8501

COPY pyproject.toml .
COPY README.md .
RUN uv sync

# Install mcp-alchemy in development mode
RUN cd /app/mcp-alchemy && uv pip install -e .

# Copy application files
COPY app.py .
COPY utils ./utils

# Set PATH to include the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Run the Streamlit application
CMD ["uv", "run", "streamlit", "run", "app.py"]
