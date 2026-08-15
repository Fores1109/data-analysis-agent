# 部署：构建 API 镜像（Streamlit 前端可另用 docker 或本地运行）
FROM python:3.12-slim

WORKDIR /app

COPY api/requirements-api.txt requirements-api.txt
RUN pip install --no-cache-dir -r requirements-api.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
