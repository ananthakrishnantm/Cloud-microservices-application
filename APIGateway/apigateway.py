import datetime
import logging
from flask import Flask, request, jsonify, Response
import pika
import requests
import grpc
from Grpc import analytics_pb2
from Grpc import analytics_pb2_grpc
import json
import seqlog
from prometheus_client import Counter, Gauge, Summary, start_http_server, generate_latest

app = Flask(__name__)

# RabbitMQ configuration
RABBITMQ_HOST = "rabbitmq"
STUDENT_QUEUE = "student_queue"


# GRPC server configuration

GRPC_SERVER_HOST ="grpcserver"
GRPC_SERVER_PORT = 50052



# Seq logging configuration
seqlog.log_to_seq(
    server_url="http://seq:5341",  # Seq server URL
    api_key=None,                 # Add API key if required
    level=logging.INFO,           # Default log level
    batch_size=10,                # Send logs in batches
    auto_flush_timeout=10,        # Flush logs every 10 seconds
    override_root_logger=True,    # Override the default root logger
)

logger = logging.getLogger(__name__)

# Server A and Server B URLs for data retrieval
SERVER_A_URL = "http://servera:5000/api/get_student"  # Replace with your actual URL
SERVER_B_URL = "http://serverb:5001/api/get_course"   # Replace with your actual URL
SERVER_B_POST_URL = "http://serverb:5001/api/course"

# Prometheus metrics
REQUEST_COUNT = Counter('request_count', 'Total number of requests', ['method', 'endpoint'])
REQUEST_LATENCY = Summary('request_latency_seconds', 'Request latency')
SERVICE_HEALTH = Gauge('service_health', 'Health status of the service (1=healthy, 0=unhealthy)')
HTTP_ERRORS = Counter('http_errors', 'Count of HTTP error responses', ['status_code'])

# Set initial health status
SERVICE_HEALTH.set(1)

# Function to send messages to RabbitMQ
def send_to_queue(queue_name, message):
    """Send a message to RabbitMQ."""
    try:
        logger.info("Attempting to send message to RabbitMQ.", extra={"queue_name": queue_name, "message": message})
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        channel = connection.channel()

        channel.queue_declare(queue=queue_name)
        channel.basic_publish(exchange='', routing_key=queue_name, body=json.dumps(message))
        logger.info("Message successfully sent to RabbitMQ.", extra={"queue_name": queue_name, "message": message})

        connection.close()
    except Exception as e:
        logger.error("Failed to send message to RabbitMQ.", exc_info=True)

# Health check endpoint
@app.route('/healthz', methods=['GET'])
def health_check():
    """Health check endpoint for system status monitoring."""
    logger.info("Health check initiated.")
    try:
        # Test basic connectivity to RabbitMQ
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        connection.close()
        logger.info("Health check passed.")
        return jsonify({"status": "healthy", "service": "API Gateway"}), 200
    except Exception as e:
        logger.error("Health check failed.", exc_info=True)
        SERVICE_HEALTH.set(0)  # Update health status to unhealthy
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

# Metrics endpoint for Prometheus
@app.route('/metrics', methods=['GET'])
def metrics():
    logger.info("Metrics endpoint accessed.")
    return Response(generate_latest(), mimetype='text/plain')

# Student Gateway
@app.route('/student', methods=['GET', 'POST'])
@REQUEST_LATENCY.time()  # Track request latency
def student_gateway():
    logger.info(f"Student endpoint accessed via {request.method}.")
    REQUEST_COUNT.labels(method=request.method, endpoint='/student').inc()
    if request.method == 'GET':
        try:
            logger.info(f"Attempting to fetch student data from {SERVER_A_URL}...")
            response = requests.get(SERVER_A_URL)
            logger.info(f"Received response from Server A: {response.status_code}")
            return jsonify(response.json()), response.status_code
        except Exception as e:
            logger.error("Error retrieving student data.", exc_info=True)
            return jsonify({"error": f"Error retrieving student data: {e}"}), 500
    elif request.method == 'POST':
        data = request.json
        if not data or 'name' not in data or 'email' not in data or 'course' not in data:
            logger.warning("Invalid payload for POST request to /student.")
            return jsonify({"error": "Missing 'name', 'email', or 'course' in payload"}), 400

        logger.info("Sending student data to RabbitMQ.", extra={"payload": data})
        send_to_queue(STUDENT_QUEUE, data)
        return jsonify({"message": "Student data sent to RabbitMQ"}), 202

# Course Gateway
@app.route('/course', methods=['GET', 'POST'])
@REQUEST_LATENCY.time()  # Track request latency
def course_gateway():
    logger.info(f"Course endpoint accessed via {request.method}.")
    REQUEST_COUNT.labels(method=request.method, endpoint='/course').inc()
    if request.method == 'GET':
        try:
            logger.info(f"Attempting to fetch course data from {SERVER_B_URL}...")
            response = requests.get(SERVER_B_URL)
            logger.info(f"Received response from Server B: {response.status_code}")
            return jsonify(response.json()), response.status_code
        except Exception as e:
            logger.error("Error retrieving course data.", exc_info=True)
            return jsonify({"error": f"Error retrieving course data: {e}"}), 500
    elif request.method == 'POST':
        try:
            logger.info("Sending course data to Server B.")
            response = requests.post(SERVER_B_POST_URL, json=request.json)
            logger.info(f"Received response from Server B: {response.status_code}")
            return jsonify(response.json()), response.status_code
        except Exception as e:
            logger.error("Error saving course data.", exc_info=True)
            return jsonify({"error": f"Error saving course data: {e}"}), 500


@app.route('/analytics', methods=['POST'])
def analytics_gateway():
    try:
        # Parse JSON request
        request_data = request.json
        request_type = request_data.get("type", None)  # e.g., "students" or "courses"

        if not request_type:
            return jsonify({"error": "Missing 'type' in request payload"}), 400

        # Connect to gRPC server
        with grpc.insecure_channel(f"{GRPC_SERVER_HOST}:{GRPC_SERVER_PORT}") as channel:
            grpc_client = analytics_pb2_grpc.StudentCourseServiceStub(channel)

            if request_type == "courses":
                grpc_request = analytics_pb2.Empty()
                grpc_response = grpc_client.GetCourseStatistics(grpc_request)
                return jsonify({
                    "courses": [
                        {
                            "id": course.id,
                            "course_name": course.course_name,
                            "course_code": course.course_code,
                            "student_count": course.student_count
                        } for course in grpc_response.courses
                    ]
                }), 200

            elif request_type == "students":
                grpc_request = analytics_pb2.Empty()
                grpc_response = grpc_client.GetStudentCourseData(grpc_request)
                return jsonify({
                    "students": [
                        {
                            "id": student.id,
                            "name": student.name,
                            "email": student.email,
                            "course": student.course
                        } for student in grpc_response.students
                    ]
                }), 200

            else:
                return jsonify({"error": f"Unknown type '{request_type}'. Supported types: 'students', 'courses'"}), 400

    except grpc.RpcError as e:
        logger.error("Error communicating with gRPC server.", exc_info=True)
        return jsonify({"error": "Failed to connect to analytics service", "details": str(e)}), 500

    except Exception as e:
        logger.error("Unexpected error occurred.", exc_info=True)
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500





if __name__ == '__main__':
    logger.info("Starting API Gateway...")
    start_http_server(8080)  # Start Prometheus metrics server
    app.run(debug=True, host='0.0.0.0', port=8080)
