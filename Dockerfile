FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py collector.py config.py ./
RUN useradd --uid 10001 --create-home worker
USER worker
ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "exec uvicorn app:create_app --factory --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --no-access-log"]
