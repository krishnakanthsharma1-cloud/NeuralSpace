FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip --no-cache-dir && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Install NeuralSpace itself
RUN pip install --no-cache-dir -e .

EXPOSE 10000

CMD ["uvicorn", "aggregator:app", "--host", "0.0.0.0", "--port", "10000"]