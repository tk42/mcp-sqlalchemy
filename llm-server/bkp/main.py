import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import ctypes
import json
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None


class Config:
    model_path: str = os.getenv("MODEL_PATH")
    max_tokens: int = 2048
    max_batch_size: int = 5
    n_threads: int = 4


config = Config()


# llama.cppのライブラリをロード
def load_llama_cpp():
    try:
        llama = ctypes.CDLL("/app/llama.cpp/build/libllama.so")
        return llama
    except Exception as e:
        logger.error(f"Failed to load llama.cpp: {e}")
        raise


class LLamaModel:
    def __init__(self, model_path: str):
        self.llama = load_llama_cpp()
        self.model_path = model_path
        self.context = None
        self.init_model()

    def init_model(self):
        if not Path(self.model_path).exists():
            raise FileNotFoundError(f"Model file not found: {self.model_path}")
        
        # モデルの初期化（実際のllama.cpp APIに合わせて実装）
        # Note: これは簡略化された例です
        self.context = self.llama.llama_init_from_file(
            self.model_path.encode(),
            ctypes.c_int(config.n_threads)
        )
        if not self.context:
            raise RuntimeError("Failed to initialize model")

    def generate(self, prompt: str, max_tokens: int = 2048) -> str:
        # 推論の実行（実際のllama.cpp APIに合わせて実装）
        result = self.llama.llama_generate(
            self.context,
            prompt.encode(),
            ctypes.c_int(max_tokens)
        )
        return result.decode() if result else ""

    def __del__(self):
        if self.context:
            self.llama.llama_free(self.context)

# FastAPIアプリケーション
app = FastAPI(title="LLM Server")

# モデルのグローバルインスタンス
model = None

# スレッドプール
executor = ThreadPoolExecutor(max_workers=config.n_threads)

@app.on_event("startup")
async def startup_event():
    global model
    try:
        model = LLamaModel(config.model_path)
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    global model
    if model:
        del model
    executor.shutdown(wait=True)

def create_prompt(query: str, context: Optional[Dict[str, Any]] = None) -> str:
    # プロンプトテンプレートの作成
    template = """
    Transform the following natural language query into a valid SQL query.
    Use the following context from previous queries if relevant:
    {context}
    
    Current query to transform:
    {query}
    
    Respond with a valid SQL query that:
    1. Is compatible with MS SQL Server 2017
    2. Includes appropriate error handling
    3. Is optimized for performance
    
    SQL Query:"""
    
    context_str = json.dumps(context, indent=2) if context else "No context available"
    return template.format(context=context_str, query=query)

@app.post("/transform")
async def transform_query(request: QueryRequest):
    if not model:
        raise HTTPException(status_code=500, detail="Model not initialized")
    
    prompt = create_prompt(request.query, request.context)
    
    try:
        # 非同期でモデルを実行
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            executor,
            model.generate,
            prompt,
            config.max_tokens
        )
        
        # 結果の後処理
        sql_query = result.strip()
        if not sql_query:
            raise HTTPException(status_code=500, detail="Failed to generate SQL query")
        
        return {
            "transformed_query": sql_query
        }
    except Exception as e:
        logger.error(f"Error during query transformation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    if not model:
        raise HTTPException(status_code=503, detail="Model not initialized")
    return {"status": "healthy"}