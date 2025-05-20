# Use the official Python image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the client code
COPY Client /app/Client

# Expose ports if necessary (e.g., for Flask-based UIs or APIs in the client)
EXPOSE 5005 

# Default command to run the client
CMD ["python", "main.py"]
