FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/app/.cache/huggingface \
    TZ=Asia/Shanghai

WORKDIR /app

# chromadb / tokenizers 在 slim 镜像里需要编译工具链
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# 关键：先装 CPU 版 torch。
# sentence-transformers 依赖 torch，默认会拉 2GB+ 的 CUDA 版本，
# 只装 CPU 版可以把镜像从 ~4GB 压到 ~1GB。
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# 运行期需要可写目录（挂载卷会覆盖，这里保证镜像本身可用）
RUN mkdir -p uploads data/chroma data/kb

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s \
    CMD curl -fsS http://127.0.0.1:8000/docs > /dev/null || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
