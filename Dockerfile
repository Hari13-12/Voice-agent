# Use official Python image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements file
COPY req.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r req.txt

# Copy the rest of the application code
COPY . .

# Set environment variables (optional, e.g., for unbuffered output)
ENV PYTHONUNBUFFERED=1

RUN python agent.py download-files

# Default command to run the agent
CMD ["python", "agent.py", "start"] 