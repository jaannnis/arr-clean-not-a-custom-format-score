FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy script
COPY cleanup_script.py .

# Create logs directory
RUN mkdir -p /logs

# Set execute permissions
RUN chmod +x cleanup_script.py

# Run script
CMD ["python", "/app/cleanup_script.py"]

