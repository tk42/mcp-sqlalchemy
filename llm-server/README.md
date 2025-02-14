## llm-server

Run this `docker-compose up` to start the LLM server on GCP VM (GPU instance)

```bash
sudo curl -sSL \
https://github.com/docker/compose/releases/download/v2.27.1/docker-compose-linux-x86_64 \
  -o /var/lib/google/docker-compose
sudo chmod o+x /var/lib/google/docker-compose
mkdir -p ~/.docker/cli-plugins
ln -sf /var/lib/google/docker-compose \
  ~/.docker/cli-plugins/docker-compose
docker compose version
```

Install gguf
```bash
curl -L -O https://huggingface.co/your-file
```

Run the LLM server
```bash
apt install -y curl
```

Phi-4
```bash
docker run -p 23178:8080 -v /home/nsplat/:/models --gpus all ghcr.io/ggerganov/llama.cpp:server-cuda -m /models/phi-4-q4.gguf -c 16384 --host 0.0.0.0 --port 8080 --n-gpu-layers 99 --jinja
```

DeepSeek-R1
```bash
docker run -p 23178:8080 -v /home/nsplat/:/models --gpus all ghcr.io/ggerganov/llama.cpp:server-cuda -m /models/DeepSeek-R1-Distill-Llama-8B-Q8_0.gguf -c 16384 --host 0.0.0.0 --port 8080 --n-gpu-layers 99 --jinja
```