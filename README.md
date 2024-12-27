# Campus Connect Backend

A Flask-based backend service for a campus communication and collaboration platform.

## Features

- User Management & Authentication
- Course Management
- Assignment Handling
- Real-time Chat System
- Media File Management
- Notification System
- Group Events & Activities

## Project Structure

```
campus-connect-backend/
├── app/
│   ├── models/          # Database models
│   ├── schemas/         # Marshmallow schemas for serialization
│   ├── services/        # Business logic layer
│   ├── controllers/     # Route handlers
│   ├── config/          # Configuration files
│   └── errors.py        # Error handling
├── instance/            # Instance-specific files
├── logs/               # Application logs
├── tests/              # Test suite
├── migrations/         # Database migrations
├── .env.example        # Example environment variables
├── .gitignore         # Git ignore rules
├── requirements.txt    # Python dependencies
└── run.py             # Application entry point
```

## Prerequisites

- Python 3.9+
- PostgreSQL
- Redis (for caching and message queuing)
- AWS S3 (for media storage)

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/campus-connect-backend.git
   cd campus-connect-backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Initialize the database:
   ```bash
   flask db upgrade
   ```

## Running the Application

### Development
```bash
flask run
# or
python run.py
```

### Production
```bash
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

## API Documentation

### Authentication
- POST /api/users/register - Register a new user
- POST /api/users/login - User login
- POST /api/users/logout - User logout

### Courses
- GET /api/courses - List all courses
- POST /api/courses - Create a new course
- GET /api/courses/<id> - Get course details
- PUT /api/courses/<id> - Update course
- DELETE /api/courses/<id> - Delete course

### Assignments
- GET /api/assignments - List assignments
- POST /api/assignments - Create assignment
- GET /api/assignments/<id> - Get assignment details
- PUT /api/assignments/<id> - Update assignment
- DELETE /api/assignments/<id> - Delete assignment

### Chat
- GET /api/chats - List user's chats
- POST /api/chats - Create new chat
- GET /api/chats/<id>/messages - Get chat messages
- POST /api/messages - Send message

### Media
- POST /api/media/upload - Upload media file
- GET /api/media/<id> - Get media details
- DELETE /api/media/<id> - Delete media

### Notifications
- GET /api/notifications - List notifications
- PUT /api/notifications/<id>/read - Mark as read
- DELETE /api/notifications/<id> - Delete notification

## Testing

Run tests with pytest:
```bash
pytest
```

With coverage report:
```bash
pytest --cov=app tests/
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Flask and its extensions
- SQLAlchemy
- Marshmallow
- Other open source libraries used in this project
