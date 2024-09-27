import sys
import os
import logging
from flask_migrate import Migrate

# Print initial diagnostics
print(f"Initial working directory: {os.getcwd()}")
print(f"Location of run.py: {__file__}")
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print(f"Initial Python path: {sys.path}")

# Set up paths
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, 'backend')

# Add the backend directory to the Python path
sys.path.insert(0, backend_dir)

# Set up logging
log_file = os.path.join(current_dir, 'app.log')
logging.basicConfig(filename=log_file, level=logging.INFO,
                    format='%(asctime)s %(levelname)s: %(message)s')

# Test log statement
logging.info("Flask app starting. Testing logging...")

from backend.api import create_app, db
from dotenv import load_dotenv
from flask_cors import CORS

# Load environment variables
print("Attempting to load .env file...")
load_dotenv(os.path.join(current_dir, '.env'))

print("Creating Flask app...")
app = create_app()
CORS(app)

# Create migration object
migrate = Migrate(app, db)

print("Flask app created successfully")
print(f"Final working directory: {os.getcwd()}")
print(f"Final Python path: {sys.path}")

if __name__ == '__main__':
    print("Starting Flask server...")
    try:
        # Run the app with debug mode
        app.run(debug=True, host="0.0.0.0", port=5001)
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}", exc_info=True)
        print(f"An error occurred: {str(e)}")
        raise