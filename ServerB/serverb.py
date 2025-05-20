from flask import Flask, request, jsonify,Response
import pymssql
import time
from prometheus_client import Counter, Gauge, Summary, generate_latest, start_http_server

# Flask app initialization
app = Flask(__name__)

# SQL Server configuration
server = 'sqlserver'  # or 'host.docker.internal' if Flask is inside Docker
username = 'sa'
password = 'My!P@ssw0rd1'

# connection_string = f'DRIVER={driver};SERVER={server};PORT=1433;UID={username};PWD={password}'



# Prometheus metrics
REQUEST_COUNT = Counter('request_count', 'Total number of requests', ['method', 'endpoint'])
REQUEST_LATENCY = Summary('request_latency_seconds', 'Request latency')


# Connect to the SQL 
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
                print("Error connecting to SQL Server:", e)
                time.sleep(5)
                attempt += 1
        raise Exception("Failed to connect to SQL Server after multiple attempts.")

conn,cursor = connect_to_sqlserver()

# Define the Course model in SQL
def create_table():
    try:
        cursor.execute('''
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='courses' AND xtype='U')
        BEGIN
            CREATE TABLE courses (
                id INT PRIMARY KEY IDENTITY(1,1),
                course_name NVARCHAR(255) NOT NULL,
                course_code NVARCHAR(50) NOT NULL UNIQUE
            
            )
        END
        ''')
        conn.commit()
        print("Courses table created successfully!")
    except Exception as e:
        print("Error creating table:", e)

# Run the table creation function
create_table()

# POST endpoint to insert course data into the database
@app.route('/api/course', methods=['POST'])
def post_course():
    REQUEST_COUNT.labels(method='POST', endpoint='/api/course').inc()
    data = request.json
    if not data or 'course_name' not in data or 'course_code' not in data:
        return jsonify({"error": "Missing 'course_name' or 'course_code' field in JSON payload"}), 400

    course_name = data['course_name']
    course_code = data['course_code']
   

    # Insert the course data into the SQL Server database
    try:
        cursor.execute("INSERT INTO courses (course_name, course_code) VALUES (%s, %s)",
                       (course_name, course_code))
        conn.commit()
        return jsonify({"message": "Course saved to SQL Server!"}), 201
    except Exception as e:
        return jsonify({"error": f"Error saving course data: {e}"}), 500

# GET endpoint to retrieve all courses
@app.route('/api/get_course', methods=['GET'])
def get_courses():
    REQUEST_COUNT.labels(method='GET', endpoint='/api/get_course').inc()
    try:
        cursor.execute("SELECT * FROM courses")
        rows = cursor.fetchall()
        result = [{"id": row[0], "course_name": row[1], "course_code": row[2]} for row in rows]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": f"Error fetching courses: {e}"}), 500


@app.route('/metrics', methods=['GET'])
def metrics():
    return Response(generate_latest(), mimetype='text/plain')


if __name__ == '__main__':
    start_http_server(5001)
    app.run(debug=True, host='0.0.0.0', port=5001)
