
!pip install flask flask-socketio pymongo openai
pip install pyjwt
pip install flask-jwt-extended
pip install gunicorn eventlet

from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from pymongo import MongoClient
import openai
import jwt
import datetime
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity

# Initialize the Flask app and set up configurations
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # Added CORS support for SocketIO
app.config['SECRET_KEY'] = 'your-secret-key'
jwt = JWTManager(app)

# Initialize OpenAI for chatbot (replace with your actual OpenAI API key)
openai.api_key = "your-openai-api-key"

# Initialize MongoDB client (replace with your MongoDB URI if needed)
client = MongoClient("mongodb://localhost:27017/")
db = client["schoolApp"]


# Route to check if the app is running
@app.route('/')
def home():
    return "Welcome to the School App"


# ------------- Step 1: User Authentication (Login) ----------------

@app.route('/login', methods=['POST'])
def login():
    username = request.json['username']
    password = request.json['password']

    # Dummy data for validation (replace this with database check in a real app)
    user = db.users.find_one({"username": username, "password": password})

    if user:
        role = user["role"]

        # Generate a JWT token with user role and expiration time
        token = jwt.encode({
            'username': username,
            'role': role,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }, app.config['SECRET_KEY'], algorithm='HS256')

        return jsonify({"token": token})

    return jsonify({"message": "Invalid credentials"}), 401


# ------------- Step 2: Attendance Management ----------------

# Route to mark attendance (only accessible by teachers)
@app.route('/attendance', methods=['POST'])
@jwt_required()
def mark_attendance():
    current_user = get_jwt_identity()  # Get the user identity from the JWT token

    if current_user['role'] != 'teacher':
        return jsonify({"message": "Unauthorized"}), 403

    student_id = request.json['student_id']
    status = request.json['status']
    date = request.json['date']

    # Save attendance record to MongoDB
    attendance = {
        "student_id": student_id,
        "status": status,
        "date": date
    }

    db.attendance.insert_one(attendance)
    return jsonify({"message": "Attendance marked successfully"})


# Route to view attendance (only accessible by teachers)
@app.route('/attendance', methods=['GET'])
@jwt_required()
def get_attendance():
    current_user = get_jwt_identity()

    if current_user['role'] != 'teacher':
        return jsonify({"message": "Unauthorized"}), 403

    date = request.args.get('date')  # Get date from query parameters
    attendance_records = db.attendance.find({"date": date})
    attendance_list = [record for record in attendance_records]

    return jsonify(attendance_list)


# ------------- Step 3: Real-Time Chat (Socket.IO) ----------------

# Handle real-time chat messages
@socketio.on('message')
def handle_message(msg):
    print(f"Received message: {msg}")
    emit('message', msg, broadcast=True)  # Broadcast message to all connected clients


# ------------- Step 4: Chatbot Integration (OpenAI GPT-3/4) ----------------

# Route to interact with the chatbot (Q&A, note generation)
@app.route('/chatbot', methods=['POST'])
@jwt_required()
def chatbot():
    current_user = get_jwt_identity()
    user_input = request.json['user_input']

    # Use OpenAI API to generate a response
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=user_input,
        max_tokens=150
    )

    answer = response.choices[0].text.strip()
    return jsonify({"answer": answer})


# Route to generate study notes from a given content (only accessible by teachers)
@app.route('/generate_notes', methods=['POST'])
@jwt_required()
def generate_notes():
    current_user = get_jwt_identity()

    if current_user['role'] != 'teacher':
        return jsonify({"message": "Unauthorized"}), 403

    content = request.json['content']

    # Use GPT-3 to generate notes or summaries
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=f"Generate notes for the following content:\n{content}",
        max_tokens=300
    )

    notes = response.choices[0].text.strip()
    return jsonify({"notes": notes})


# ------------- Step 5: Role-Based Access Control ----------------

# Route to delete notes (only accessible by teachers)
@app.route('/delete_note', methods=['DELETE'])
@jwt_required()
def delete_note():
    current_user = get_jwt_identity()

    if current_user['role'] != 'teacher':
        return jsonify({"message": "Unauthorized"}), 403

    note_id = request.json['note_id']
    db.notes.delete_one({"_id": note_id})
    return jsonify({"message": "Note deleted successfully"})


# ------------- Step 6: Running the Flask Application ----------------

if __name__ == '__main__':
    # Running the Flask server with Socket.IO for development
    socketio.run(app, host="0.0.0.0", port=5000)
