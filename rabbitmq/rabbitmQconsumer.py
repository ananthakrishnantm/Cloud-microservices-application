import pika
import json
import requests

# RabbitMQ configuration
rabbitmq_host = 'localhost'
rabbitmq_queue = 'student_queue'

# Flask API endpoint
flask_api_url = 'http://localhost:5000/api/student'

# Callback function to process messages
def callback(ch, method, properties, body):
    try:
        # Deserialize the message
        message = json.loads(body)
        print(f"Received message from RabbitMQ: {message}")

        # Forward the message to the Flask API
        response = requests.post(flask_api_url, json=message)
        
        if response.status_code == 201:
            print(f"Successfully forwarded to Flask API: {response.json()}")
            # Acknowledge the message
            ch.basic_ack(delivery_tag=method.delivery_tag)
        else:
            print(f"Error from Flask API: {response.status_code}, {response.text}")
            # Optionally, reject or requeue the message if needed

    except Exception as e:
        print(f"Error processing message: {e}")
        # Optionally reject the message or log for later debugging

# Connect to RabbitMQ
try:
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
    channel = connection.channel()

    # Declare the queue (ensure it exists)
    channel.queue_declare(queue=rabbitmq_queue, durable=True)

    print(f"Connected to RabbitMQ, waiting for messages in queue: {rabbitmq_queue}")

    # Start consuming messages
    channel.basic_consume(queue=rabbitmq_queue, on_message_callback=callback)
    channel.start_consuming()
except Exception as e:
    print(f"Error connecting to RabbitMQ: {e}")
