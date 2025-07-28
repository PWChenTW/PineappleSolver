FROM python:3.11-slim

WORKDIR /app

# 安裝依賴
COPY ../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製源代碼
COPY ../src ./src
COPY ../run_api.py .

# 暴露端口
EXPOSE 8000

# 啟動 API
CMD ["python", "run_api.py"]