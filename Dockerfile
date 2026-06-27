FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for git (needed for the GitHub App to clone repos)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the code
COPY . .

# Install NeuralSpace itself
RUN pip install -e .

# Expose the port for the Aggregator
EXPOSE 10000

# Run the Universe Aggregator
CMD ["uvicorn", "aggregator:app", "--host", "0.0.0.0", "--port", "10000"]