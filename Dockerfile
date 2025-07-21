# ---- Build stage ----
FROM python:3.10-slim AS builder

WORKDIR /app

ENV UV_PROJECT_ENVIRONMENT=/usr/local

# システム依存パッケージ（必要最小限）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libffi-dev libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

# 依存関係ファイルをコピー
COPY pyproject.toml ./

RUN pip install --no-cache-dir uv && uv sync

# ---- Runtime stage ----
FROM python:3.10-slim

WORKDIR /app

# 必要なランタイムパッケージのみ
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# builderからsite-packagesとuvコマンドをコピー
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin/uv /usr/local/bin/uv
COPY --from=builder /usr/local/bin/streamlit /usr/local/bin/streamlit

# アプリ本体
COPY . .

# .envファイルをコピー（本番はsecretsで上書き推奨）
COPY .env.example .env

# print文やバッファ詰まり対策: PYTHONUNBUFFERED=1
ENV PYTHONUNBUFFERED=1

# ポート公開（FastAPI:8000, MCP:stdio, Streamlit:8501）
EXPOSE 8000 8501

# デフォルトはrun_app.py（自動起動スクリプト）
CMD ["python", "run_app.py"] 