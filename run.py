import os
from app import create_app
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get environment from environment variable or default to development
env = os.environ.get('FLASK_ENV', 'development')

# Create application instance
app = create_app(env)

if __name__ == '__main__':
    # Get port from environment variable or default to 5000
    port = int(os.environ.get('PORT', 5000))
    
    # Get debug mode from environment variable or default based on environment
    debug = os.environ.get('FLASK_DEBUG', env == 'development')
    
    # Run the application
    app.run(
        host='0.0.0.0',  # Make server externally visible
        port=port,
        debug=debug
    )
