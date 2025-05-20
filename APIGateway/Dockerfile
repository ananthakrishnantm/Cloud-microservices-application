# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the APIGateway folder into the container
COPY ./APIGateway /app

# Copy the Grpc folder into the container
COPY ./Grpc /app/Grpc

# Verify the directory structure
RUN ls -la /app && ls -la /app/Grpc

# Install any needed dependencies specified in requirements.txt
COPY ./APIGateway/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Add /app and /app/Grpc to the Python path
ENV PYTHONPATH="/app:/app/Grpc"

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Define environment variables for Flask
ENV FLASK_APP=apigateway.py
ENV FLASK_RUN_HOST=0.0.0.0

# Run api_gateway when the container launches
CMD ["flask", "run"]
