import sys
import os
import logging
from flask_migrate import Migrate

# Set up paths
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, 'backend')
sys.path.insert(0, backend_dir)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger('voxbox')

logger.info("Flask app starting...")

from backend.api import create_app, db
from dotenv import load_dotenv
from flask_cors import CORS

# Load environment variables (for local development)
load_dotenv(os.path.join(current_dir, '.env'))

app = create_app()
CORS(app)

# Create migration object
migrate = Migrate(app, db)

if __name__ == '__main__':
    logger.info("Starting Flask server...")
    try:
        app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5001)))
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        raise