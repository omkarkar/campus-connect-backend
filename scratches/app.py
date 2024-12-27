from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from datetime import datetime

# Initialize the app
app = Flask(__name__)

# Setup the Database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///campus_connect.db'  # SQLite for simplicity
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database and marshmallow
db = SQLAlchemy(app)
ma = Marshmallow(app)

# --------------------------------- Models -----------------------------------

# Course Model (Ensure it is defined before Assignment Model)
class Course(db.Model):
    course_id = db.Column(db.Integer, primary_key=True)
    professor_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    semester = db.Column(db.String(50))
    date_and_year = db.Column(db.DateTime)
    course_name = db.Column(db.String(255))

# Assignment Model
class Assignment(db.Model):
    assignment_id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.course_id'))
    title = db.Column(db.String(255))
    description = db.Column(db.Text)
    due_date = db.Column(db.DateTime)
    max_score = db.Column(db.Integer)
    total_points = db.Column(db.Integer)
    status = db.Column(db.Boolean)
    created_on = db.Column(db.DateTime, default=datetime.utcnow)

# User Model
class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    phone_number = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(255), unique=True)
    status = db.Column(db.String(255))
    last_seen = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Chat Model
class Chat(db.Model):
    chat_id = db.Column(db.Integer, primary_key=True)
    chat_type = db.Column(db.String(20))
    chat_name = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Message Model
class Message(db.Model):
    message_id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.chat_id'))
    sender_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    message_type = db.Column(db.String(20))
    content = db.Column(db.Text)
    media_url = db.Column(db.String(255))
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    delivered_at = db.Column(db.DateTime)
    read_at = db.Column(db.DateTime)

# Media Model
class Media(db.Model):
    media_id = db.Column(db.Integer, primary_key=True)
    media_url = db.Column(db.String(255))
    media_type = db.Column(db.String(50))
    file_size = db.Column(db.Integer)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

# Notification Model
class Notification(db.Model):
    notification_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.chat_id'))
    message_id = db.Column(db.Integer, db.ForeignKey('message.message_id'))
    notification_type = db.Column(db.String(50))
    seen = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Group Event Model
class GroupEvent(db.Model):
    event_id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.chat_id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    event_type = db.Column(db.String(50))
    event_time = db.Column(db.DateTime)

# --------------------------------- Marshmallow Schemas -----------------------------------

# Course Schema
class CourseSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Course
        include_relationships = True
        load_instance = True

# Assignment Schema
class AssignmentSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Assignment
        include_relationships = True
        load_instance = True

# User Schema
class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = User
        include_relationships = True
        load_instance = True

# Chat Schema
class ChatSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Chat
        include_relationships = True
        load_instance = True

# Message Schema
class MessageSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Message
        include_relationships = True
        load_instance = True

# Media Schema
class MediaSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Media
        include_relationships = True
        load_instance = True

# Notification Schema
class NotificationSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Notification
        include_relationships = True
        load_instance = True

# Group Event Schema
class GroupEventSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = GroupEvent
        include_relationships = True
        load_instance = True

# Initialize schemas
course_schema = CourseSchema()
courses_schema = CourseSchema(many=True)
assignment_schema = AssignmentSchema()
assignments_schema = AssignmentSchema(many=True)
user_schema = UserSchema()
users_schema = UserSchema(many=True)
chat_schema = ChatSchema()
chats_schema = ChatSchema(many=True)
message_schema = MessageSchema()
messages_schema = MessageSchema(many=True)
media_schema = MediaSchema()
medias_schema = MediaSchema(many=True)
notification_schema = NotificationSchema()
notifications_schema = NotificationSchema(many=True)
group_event_schema = GroupEventSchema()
group_events_schema = GroupEventSchema(many=True)

# --------------------------------- Routes -----------------------------------

# Create a Course
@app.route('/courses', methods=['POST'])
def add_course():
    try:
        professor_id = request.json['professor_id']
        semester = request.json['semester']
        date_and_year = datetime.strptime(request.json['date_and_year'], '%Y-%m-%d %H:%M:%S')
        course_name = request.json['course_name']

        new_course = Course(
            professor_id=professor_id,
            semester=semester,
            date_and_year=date_and_year,
            course_name=course_name
        )
        db.session.add(new_course)
        db.session.commit()

        return course_schema.jsonify(new_course), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Create an Assignment
@app.route('/assignments', methods=['POST'])
def add_assignment():
    try:
        course_id = request.json['course_id']
        title = request.json['title']
        description = request.json['description']
        due_date = datetime.strptime(request.json['due_date'], '%Y-%m-%d %H:%M:%S')
        max_score = request.json['max_score']
        total_points = request.json['total_points']
        status = request.json['status']
        
        new_assignment = Assignment(
            course_id=course_id,
            title=title,
            description=description,
            due_date=due_date,
            max_score=max_score,
            total_points=total_points,
            status=status
        )
        db.session.add(new_assignment)
        db.session.commit()

        return assignment_schema.jsonify(new_assignment), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# --------------------------------- Main Program -----------------------------------

# Ensure app context is available when creating tables
with app.app_context():
    db.create_all()  # Creates the tables in the database

if __name__ == '__main__':
    app.run(debug=True)
