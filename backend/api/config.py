import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your_secret_key_here')
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    
    # Use SQLite for both local and Azure environments
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Define the path to the data directory
    DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')

    # Session configuration
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = os.path.join(DATA_DIR, 'flask_session')
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'voxpop_'
    
    # OpenAI configuration
    OPENAI_MODEL = 'gpt-3.5-turbo'
    
    # OpenAI Assistant IDs
    ASSISTANTS = {
        "question_transformer": os.environ.get("QUESTION_TRANSFORMER_ID"),
        "question_config_generator": os.environ.get("QUESTION_CONFIG_GENERATOR_ID"),
        "survey_analyst": os.environ.get("SURVEY_ANALYST_ID")
    }
    
    # Survey configuration
    NUM_SURVEY_RESPONDENTS = int(os.environ.get('NUM_SURVEY_RESPONDENTS', 100))
    
    # Other configuration parameters
    MAX_RETRIES = int(os.environ.get('MAX_RETRIES', 3))
    
    @staticmethod
    def init_app(app):
        # Ensure session file directory exists
        os.makedirs(Config.SESSION_FILE_DIR, exist_ok=True)