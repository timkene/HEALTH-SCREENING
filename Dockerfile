FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./

# Install system dependencies needed to build numpy/pandas
RUN apt-get update && apt-get install -y build-essential gcc g++ \
    && pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir --upgrade numpy \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY . .

EXPOSE 8000

CMD ["python", "app.py"]
