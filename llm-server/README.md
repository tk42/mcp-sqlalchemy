## llm-server

Run this `docker-compose up` to start the LLM server on GCP VM (GPU instance)

### Download gguf models
```bash
apt install -y curl
curl -L -O https://huggingface.co/your-file
```

For example: you can download DeepSeek-R1 model:
```bash
curl -L -O https://huggingface.co/unsloth/DeepSeek-R1-Distill-Llama-8B-GGUF/resolve/main/DeepSeek-R1-Distill-Llama-8B-Q8_0.gguf
```
This web page is [https://huggingface.co/unsloth/DeepSeek-R1-Distill-Llama-8B-GGUF](https://huggingface.co/unsloth/DeepSeek-R1-Distill-Llama-8B-GGUF)


### Run the LLM server
Make sure install `docker`.

 - Phi-4
```bash
docker run -p 23178:8080 -v /home/nsplat/:/models --gpus all ghcr.io/ggerganov/llama.cpp:server-cuda -m /models/phi-4-q4.gguf -c 16384 --host 0.0.0.0 --port 8080 --n-gpu-layers 99 --jinja
```

 - DeepSeek-R1
```bash
docker run -p 23178:8080 -v /home/nsplat/:/models --gpus all ghcr.io/ggerganov/llama.cpp:server-cuda -m /models/DeepSeek-R1-Distill-Llama-8B-Q8_0.gguf -c 16384 --host 0.0.0.0 --port 8080 --n-gpu-layers 99 --jinja
```