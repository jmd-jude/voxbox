import os
import openai
from dotenv import load_dotenv
import json
import logging
from .config import Config
from .models import SurveyData

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)

ASSISTANT_ID = Config.ASSISTANTS["question_transformer"]

def transform_question(user_question):
    logger.info(f"Transforming question: {user_question}")

    prompt = f""" 
    Transform this user input into a high-quality polling question:
    "{user_question}"

    Requirements:
    1. Clarify the intent and use neutral, objective language.
    2. Frame for a broad audience and be specific.
    3. Classify the question type (e.g., Likert scale, multiple choice, yes/no).
    4. Provide 3-5 answer options in this format:
       a) Option 1
       b) Option 2
       c) Option 3
    5. If the question type doesn't suit multiple options, provide appropriate fallback options.

    Respond only with a JSON object, without any code block formatting or extra text. The keys in the JSON should be "question", "type", and "options".
    """

    try:
        thread = client.beta.threads.create()
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=prompt
        )
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID
        )
        while run.status != "completed":
            run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        logger.info(f"Raw messages response: {messages}")
        if not messages.data or not messages.data[0].content or not messages.data[0].content[0].text.value:
            raise ValueError("Invalid response received from API")
        response = messages.data[0].content[0].text.value
        transformed = json.loads(response)
        logger.info(f"Transformed question: {transformed}")
        return transformed
    except Exception as e:
        logger.error(f"Error in OpenAI API call: {str(e)}")
        raise

def save_transformed_question(user_id, session_id, transformed_question):
    try:
        SurveyData.save_data(user_id=user_id, session_id=session_id, data_type='transformed_question', content=transformed_question)
        logger.info(f"Transformed question saved to database for user {user_id}, session {session_id}")
    except Exception as e:
        logger.error(f"Error saving transformed question to database: {str(e)}")
        raise

def process_and_save_question(user_id, session_id, user_question):
    try:
        transformed_question = transform_question(user_question)
        save_transformed_question(user_id, session_id, transformed_question)
        SurveyData.save_data(user_id=user_id, session_id=session_id, data_type='original_question', content=user_question)
        logger.info(f"Original question saved to database for user {user_id}, session {session_id}")
        return transformed_question
    except Exception as e:
        logger.error(f"Error in process_and_save_question: {str(e)}")
        raise