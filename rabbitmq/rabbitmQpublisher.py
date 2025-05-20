import pika
import json

# RabbitMQ configuration
rabbitmq_host = 'localhost'
rabbitmq_queue = 'student_queue'

# Student data to send
student_data = {
    "name": "John Doe",
    "email": "john.doe@example.com",
    "course": "Mathematics"
}

# Publish message to RabbitMQ
try:
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
    channel = connection.channel()

    # Declare the queue (ensure it exists)
    channel.queue_declare(queue=rabbitmq_queue, durable=True)

    # Publish the message
    channel.basic_publish(
        exchange='',
        routing_key=rabbitmq_queue,
        body=json.dumps(student_data),
        properties=pika.BasicProperties(delivery_mode=2)  # Make message persistent
    )
    print(f"Message sent to RabbitMQ: {student_data}")
    connection.close()
except Exception as e:
    print(f"Error sending message to RabbitMQ: {e}")
