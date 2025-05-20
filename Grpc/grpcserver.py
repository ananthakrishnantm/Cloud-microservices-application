import grpc
from concurrent import futures
import time
import requests
import json
import pika
from analytics_pb2 import (
    Student,
    Course,
    StudentCourseResponse,
    CourseStatisticsResponse,
    StudentUpdate,
)
from analytics_pb2_grpc import StudentCourseServiceServicer, add_StudentCourseServiceServicer_to_server

SERVER_A_URL = "http://servera:5000/api/get_student"
SERVER_B_URL = "http://serverb:5001/api/get_course"

class StudentCourseService(StudentCourseServiceServicer):
    def GetStudentCourseData(self, request, context):
        """Fetch aggregated data from Server A and Server B"""
        try:
            students = requests.get(SERVER_A_URL).json()
            response = StudentCourseResponse()
            for student in students:
                response.students.add(
                    id=student['id'],
                    name=student['name'],
                    email=student['email'],
                    course=student['course']
                )
            return response
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return StudentCourseResponse()

    def GetCourseStatistics(self, request, context):
        """Generate course statistics from Server B"""
        try:
            courses = requests.get(SERVER_B_URL).json()
            response = CourseStatisticsResponse()
            for course in courses:
                # Count students enrolled per course (example logic)
                response.courses.add(
                    id=course['id'],
                    course_name=course['course_name'],
                    course_code=course['course_code'],
                    student_count=0  # You can implement counting if needed
                )
            return response
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return CourseStatisticsResponse()

    def StreamRealTimeUpdates(self, request, context):
        """Stream real-time updates from RabbitMQ"""
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
        channel = connection.channel()
        channel.queue_declare(queue='student_queue')

        def callback(ch, method, properties, body):
            student_data = json.loads(body)
            update = StudentUpdate(
                student_id=student_data['id'],
                name=student_data['name'],
                email=student_data['email'],
                course=student_data['course']
            )
            context.write(update)
            ch.basic_ack(delivery_tag=method.delivery_tag)

        channel.basic_consume(queue='student_queue', on_message_callback=callback, auto_ack=False)
        try:
            channel.start_consuming()
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)

# Run the gRPC server
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_StudentCourseServiceServicer_to_server(StudentCourseService(), server)
    server.add_insecure_port('[::]:50052')
    server.start()
    print("gRPC server started on port 5005.")
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    serve()
