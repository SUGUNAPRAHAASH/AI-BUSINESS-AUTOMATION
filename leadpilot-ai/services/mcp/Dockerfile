FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN pip install --upgrade pip && \
    pip install mcp httpx

COPY server.py .

EXPOSE 8765

CMD ["python", "server.py"]
