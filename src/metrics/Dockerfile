FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY metrics.py .

# Expose the internal port
EXPOSE 8001

# Run the server
# CMD ["python", "metrics.py"]
CMD ["python", "metrics.py"]