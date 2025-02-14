# MCP-SQLAlchemy

A sample project that builds MCP clients with llamacpp and runekaagaard/mcp-alchemy.

## Description

This project demonstrates the integration of MCP (Model, Controller, Presenter) architecture with SQLAlchemy, using LLaMa.cpp for AI capabilities.

## Requirements

- Python >= 3.12
- Docker and Docker Compose (for running the database and LLM server)

## Dependencies

- openai >= 1.57.0
- mcp >= 1.2.1
- python-dotenv >= 1.0.1
- sqlalchemy >= 2.0.36
- httpx >= 0.24.1
- streamlit >= 1.31.1

## Installation

1. Clone the repository
2. Create a virtual environment
3. Install dependencies using uv:
   ```bash
   uv sync
   ```

## Usage

Run the Streamlit application:
```bash
streamlit run app.py
```

## GPU Instance setup on GCP
```bash
docker run -p 23178:8080 -v /path/to/models:/models --gpus all ghcr.io/ggerganov/llama.cpp:server-cuda -m models/phi-4-Q2_K.gguf -c 32178 --host 0.0.0.0 --port 8080 --n-gpu-layers 99
```

## License

See the LICENSE file for details.