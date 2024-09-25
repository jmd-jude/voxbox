# config.py
import os

class Config:
    SECRET_KEY = 'your_secret_key_here'
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')  # Add this line

    # ...rest of your config...
    
    # Define the path to the data directory
    DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')

    # Session configuration
    SESSION_TYPE = 'filesystem'  # Storing session data in the server's file system
    SESSION_FILE_DIR = os.path.join(DATA_DIR, 'flask_session')  # Directory for session files
    SESSION_PERMANENT = False  # Sessions expire when the browser is closed
    SESSION_USE_SIGNER = True  # Sign the session cookie for added security
    
    # OpenAI configuration
    OPENAI_MODEL = 'gpt-3.5-turbo'
    
    # OpenAI Assistant IDs
    ASSISTANTS = {
        "question_transformer": "asst_GEqxbSSDWkKNAcxWdWJqMhYd",
        # Add more assistants here as needed
    }
    
    # Survey configuration
    NUM_SURVEY_RESPONDENTS = 10
    
    # Other configuration parameters
    MAX_RETRIES = 3
    
    # Add more configuration variables as needed
    @staticmethod
    def init_app(app):
        # Ensure session file directory exists
        if not os.path.exists(Config.SESSION_FILE_DIR):
            os.makedirs(Config.SESSION_FILE_DIR)