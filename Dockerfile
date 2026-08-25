FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir pytest httpx pytest-asyncio

COPY . .

EXPOSE 4006

# Run uvicorn on the api package
CMD ["uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "4006"]
