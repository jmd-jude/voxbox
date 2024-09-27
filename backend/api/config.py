# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = 'your_secret_key_here'
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///../instance/app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Define the path to the data directory
    DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')

    # Session configuration
    SESSION_TYPE = 'filesystem'  # Storing session data in the server's file system
    DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
    SESSION_FILE_DIR = os.path.join(DATA_DIR, 'flask_session')  # Directory for session files
    SESSION_PERMANENT = False  # Sessions expire when the browser is closed
    SESSION_USE_SIGNER = True  # Sign the session cookie for added security
    SESSION_KEY_PREFIX = 'voxpop_'
    
    # OpenAI configuration
    OPENAI_MODEL = 'gpt-3.5-turbo'
    
    # OpenAI Assistant IDs
    # Add more assistants here as needed
    ASSISTANTS = {
        "question_transformer": os.getenv("QUESTION_TRANSFORMER_ID"),
        "question_config_generator": os.getenv("QUESTION_CONFIG_GENERATOR_ID"),
        "survey_analyst": os.getenv("SURVEY_ANALYST_ID")
    }
    
    # Survey configuration
    NUM_SURVEY_RESPONDENTS = 100
    
    # Other configuration parameters
    MAX_RETRIES = 3
    
    # Add more configuration variables as needed
    @staticmethod
    def init_app(app):
        # Ensure session file directory exists
        if not os.path.exists(Config.SESSION_FILE_DIR):
            os.makedirs(Config.SESSION_FILE_DIR)