from flask import Flask, render_template, request, redirect, url_for, jsonify
import requests

app = Flask(__name__)

# API Gateway URLs
API_GATEWAY_BASE_URL = "http://apigateway:8080"  # Update with the actual API Gateway URL
STUDENT_API_URL = f"{API_GATEWAY_BASE_URL}/student"
COURSE_API_URL = f"{API_GATEWAY_BASE_URL}/course"


@app.route('/')
def home():
    """Render the homepage with links to student and course management."""
    return render_template("index.html")



@app.route('/students', methods=['GET', 'POST'])
def manage_students():
    """Manage students: Add new students and view existing ones."""
    if request.method == 'POST':
        # Collect form data
        student_data = {
            "name": request.form["name"],
            "email": request.form["email"],
            "course": request.form["course"]
        }
        # Send POST request to API Gateway
        response = requests.post(STUDENT_API_URL, json=student_data)
        if response.status_code == 202:
            return redirect(url_for("manage_students"))
        else:
            return render_template("error.html", message=response.json().get("error", "Failed to add student"))

    # Fetch all students
    response = requests.get(STUDENT_API_URL)
    if response.status_code == 200:
        students = response.json()
        return render_template("students.html", students=students)
    else:
        return render_template("error.html", message=response.json().get("error", "Failed to fetch students"))


@app.route('/courses', methods=['GET', 'POST'])
def manage_courses():
    """Manage courses: Add new courses and view existing ones."""
    if request.method == 'POST':
        # Collect form data
        course_data = {
            "course_name": request.form["course_name"],
            "course_code": request.form["course_code"]
        }
        # Send POST request to API Gateway
        response = requests.post(COURSE_API_URL, json=course_data)

        # Debug the API response
        app.logger.info(f"POST /course response status: {response.status_code}")
        app.logger.info(f"POST /course response body: {response.text}")

        try:
            response_data = response.json()
        except ValueError:  # Handle JSON parsing errors
            response_data = {"error": "Invalid response from API Gateway"}

        # Check for success
        if response.status_code in [200, 201, 202]:
            return redirect(url_for("manage_courses"))
        else:
            error_message = response_data.get("error", "Failed to add course")
            return render_template("error.html", message=error_message)

    # Fetch all courses
    response = requests.get(COURSE_API_URL)
    app.logger.info(f"GET /course response status: {response.status_code}")
    if response.status_code == 200:
        courses = response.json()
        return render_template("courses.html", courses=courses)
    else:
        error_message = response.json().get("error", "Failed to fetch courses")
        return render_template("error.html", message=error_message)

@app.route('/analytics', methods=['GET', 'POST'])
def analytics():
    """Render the analytics page and display course or student statistics."""
    if request.method == 'POST':
        # Collect form data
        request_type = request.form["type"]

        # Send POST request to the analytics gateway
        response = requests.post(f"{API_GATEWAY_BASE_URL}/analytics", json={"type": request_type})
        
        if response.status_code == 200:
            data = response.json()
            return render_template("analytics.html", data=data, request_type=request_type)
        else:
            error_message = response.json().get("error", "Failed to fetch analytics data")
            return render_template("error.html", message=error_message)

    # Default view: no data
    return render_template("analytics.html", data=None)












if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5005)
