# src/Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY src/ .

RUN pip install "fastapi[all]"

EXPOSE 80

CMD ["uvicorn", "dumper_app:app", "--host", "0.0.0.0", "--port", "80"]