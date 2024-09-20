import sys
import os
import logging

# Set up logging before any other operations
logging.basicConfig(filename='app.log', level=logging.INFO, 
                    format='%(asctime)s %(levelname)s: %(message)s')

# Test log statement to ensure logging works
logging.info("Flask app starting. Testing logging...")

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from api import create_app
from dotenv import load_dotenv
from flask_cors import CORS

# Print statements for debugging
print("Starting run.py")
print(f"Current working directory: {os.getcwd()}")
print("Python path:", sys.path)
print("Attempting to load .env file...")
load_dotenv()

try:
    print("Creating Flask app...")
    app = create_app()
    
    # Enable CORS for the entire app
    CORS(app)

    print("Flask app created successfully")

    if __name__ == '__main__':
        print("Starting Flask server...")
        app = create_app()
        # Run the app with debug mode on port 5001
        app.run(debug=True, host="0.0.0.0", port=5001)

except Exception as e:
    logging.error(f"An error occurred: {str(e)}", exc_info=True)
    print(f"An error occurred: {str(e)}")
    raise
