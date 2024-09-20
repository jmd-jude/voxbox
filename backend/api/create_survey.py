import os
import openai
from dotenv import load_dotenv
import json
import logging
from .config import Config

# Set up logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

# Set up OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

ASSISTANT_ID = Config.ASSISTANTS["question_transformer"]

def transform_question(user_question):
    logging.info(f"Transforming question: {user_question}")

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
        # Create a thread
        thread = client.beta.threads.create()

        # Add the message to the thread
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=prompt
        )

        # Run the assistant
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID
        )

        # Wait for the run to complete
        while run.status != "completed":
            run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

        # Retrieve the messages
        messages = client.beta.threads.messages.list(thread_id=thread.id)

        # Log the raw response for debugging
        logging.info(f"Raw messages response: {messages}")

        # Validate response
        if not messages.data or not messages.data[0].content or not messages.data[0].content[0].text.value:
            logging.error("No valid response received from OpenAI API")
            raise ValueError("Invalid response received from API")

        # Get the last message from the assistant
        response = messages.data[0].content[0].text.value

        # Parse the JSON response
        transformed = json.loads(response)
        logging.info(f"Transformed question: {transformed}")
        return transformed

    except Exception as e:
        logging.error(f"Error in OpenAI API call: {str(e)}")
        raise
