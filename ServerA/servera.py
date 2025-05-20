from flask import Flask, jsonify,Response
import pymssql
import pika
import time
import threading
import json
from prometheus_client import Counter, Gauge, Summary, generate_latest, start_http_server

# Flask app initialization
app = Flask(__name__)

# SQL Server configuration
server = 'sqlserver'  # or 'host.docker.internal' if Flask is inside Docker
username = 'sa'
password = 'My!P@ssw0rd1'

# Prometheus metrics
REQUEST_COUNT = Counter('request_count', 'Total number of requests', ['method', 'endpoint'])
REQUEST_LATENCY = Summary('request_latency_seconds', 'Request latency')

def connect_to_sqlserver():
    attempt = 0
    while attempt < 100:
        try:
            print(f"Attempt {attempt + 1}: Connecting to SQL Server...")
            conn = pymssql.connect(server=server, user=username, password=password)
            cursor = conn.cursor()
            print("Connected to SQL Server successfully!")
            return conn, cursor
        except Exception as e:
            print(f"Error: {e}. Retrying...")
            time.sleep(5)
            attempt += 1
    raise Exception("Failed to connect to SQL Server after multiple attempts.")

# Try connecting to SQL Server
conn, cursor = connect_to_sqlserver()

def create_table():
    try:
        cursor.execute('''
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='students' AND xtype='U')
        BEGIN
            CREATE TABLE students (
                id INT PRIMARY KEY IDENTITY(1,1),
                name NVARCHAR(255) NOT NULL,
                email NVARCHAR(255) NOT NULL UNIQUE,
                course NVARCHAR(100) NOT NULL
            )
        END
        ''')
        conn.commit()
        print("Students table created successfully!")
    except Exception as e:
        print("Error creating table:", e)

# Run the table creation function
create_table()

def insert_student_to_db(student_data):
    try:
        cursor.execute("INSERT INTO students (name, email, course) VALUES (%s, %s, %s)",
                       (student_data['name'], student_data['email'], student_data['course']))
        conn.commit()
        print(f"Student {student_data['name']} added to the database!")
    except Exception as e:
        print(f"Error inserting student data into DB: {e}")

# Function to consume messages from RabbitMQ queue
def consume_from_queue():
    while True:
        try:
            print("Attempting to connect to RabbitMQ...")
            connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))  # or the IP address of the container
            channel = connection.channel()

            # Declare the queue if not already declared
            channel.queue_declare(queue='student_queue')

            def callback(ch, method, properties, body):
                try:
                    student_data = json.loads(body)  # Parse the message as JSON
                    print(f"Received student data: {student_data}")
                    insert_student_to_db(student_data)  # Insert data into SQL Server
                    ch.basic_ack(delivery_tag=method.delivery_tag)  # Acknowledge the message
                except Exception as e:
                    print(f"Error processing message: {e}")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

            # Start consuming messages from the queue
            channel.basic_consume(queue='student_queue', on_message_callback=callback, auto_ack=False)
            print("Waiting for messages from RabbitMQ...")
            channel.start_consuming()

        except Exception as e:
            print(f"Error consuming messages from RabbitMQ: {e}.Retrying in 5 seconds...")
            time.sleep(5)

# Run the consumer in a separate thread to listen for RabbitMQ messages
rabbitmq_thread = threading.Thread(target=consume_from_queue)

if not rabbitmq_thread.is_alive():
    print("RabbitMQ thread stopped unexpectedly!")

rabbitmq_thread.daemon = True  # Daemonize the thread to exit with the main program
rabbitmq_thread.start()

# GET endpoint to retrieve all student data (optional for testing purposes)
@app.route('/api/get_student', methods=['GET'])
def get_student():
    REQUEST_COUNT.labels(method='GET', endpoint='/api/get_student').inc()
    
    try:
        cursor.execute("SELECT * FROM students")
        rows = cursor.fetchall()
        result = [{"id": row[0], "name": row[1], "email": row[2], "course": row[3]} for row in rows]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": f"Error fetching student data: {e}"}), 500

# Metrics endpoint for Prometheus
@app.route('/metrics', methods=['GET'])
def metrics():
    return Response(generate_latest(), mimetype='text/plain')

if __name__ == '__main__':
    # Start the Prometheus metrics server on a different port (8001 for example)
    start_http_server(5000)  # Prometheus scrapes metrics from this port
    app.run(debug=True, host='0.0.0.0', port=5000)
