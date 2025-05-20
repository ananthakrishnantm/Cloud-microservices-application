# Use a base Python image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the gRPC server code
COPY ./Grpc /app

# Expose the gRPC port
EXPOSE 50052

# Start the gRPC server
CMD ["python", "grpcserver.py"]
