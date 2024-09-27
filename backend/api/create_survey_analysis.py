import json
import time
import logging
import openai
from dotenv import load_dotenv
from .config import Config
from .models import SurveyData
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# Set up OpenAI client
client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
ASSISTANT_ID = Config.ASSISTANTS["survey_analyst"]

def load_survey_data(user_id, session_id):
    try:
        question_data = SurveyData.get_data(session_id, 'transformed_question', user_id)
        results = SurveyData.get_data(session_id, 'survey_results', user_id)
        logging.info("Loaded survey data: "
                     "Question: %s, "
                     "Aggregate results: %d, "
                     "Individual responses: %d",
                     question_data['question'],
                     len(results["aggregate_results"]['answers']),
                     len(results['individual_responses']))
        return {
            'question': question_data,
            'aggregate_results': results['aggregate_results'],
            'individual_responses': results['individual_responses']
        }
    except Exception as e:
        logging.error(f"Unexpected error loading survey data: {str(e)}")
        raise

def format_analysis_prompt(survey_data):
    prompt = f"""
    IMPORTANT: Your entire response must be a single, complete JSON object provided in one message. Do not split your response across multiple messages. Limit your response to 800 words maximum.

    Analyze the following survey data and provide a brief, engaging summary in a single JSON object with the following structure:

    {{
      "key_finding": "A punchy, exciting insight with a percentage in fewer than 7 words.",
      "quick_stats": [
        "First interesting statistic from the results.",
        "Second interesting statistic from the results.",
        "Third interesting statistic from the results."
      ],
      "interpretation": [
        {{
          "name": "Name",
          "age": "Age",
          "description": "Brief phrase describing who they are and where they're from",
          "quote": "First-person quote reflecting their perspective on the survey topic"
        }},
        // Include 5 such entries
      ],
      "fun_fact": "An interesting or surprising takeaway from the focus group leader."
    }}

    Survey Question: {survey_data['question']['question']}
    Aggregate Results:
    {json.dumps(survey_data['aggregate_results'], indent=2)}

    Guidelines:
    1. Key Finding: Identify the most surprising insight, including a percentage.
    2. Quick Stats: Summarize three engaging statistics as if sharing exciting focus group moments.
    3. Interpretation: Create five diverse testimonials from imaginary focus group participants.
    4. Fun Fact: Provide a reflection from the perspective of the focus group leader.

    Ensure your response is a single, well-formed JSON object with no text before or after. If data is unavailable, use placeholders to maintain the JSON structure.
    """
    logging.info("Analysis prompt formatted successfully.")
    return prompt

def get_analysis_from_assistant(prompt):
    try:
        thread = client.beta.threads.create()
        message = client.beta.threads.messages.create(
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
            time.sleep(1)
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        last_message = messages.data[0]
        response = last_message.content[0].text.value
        logging.info("Analysis received from assistant. Response: %s", response)  # Log the raw response
        return response
    except Exception as e:
        logging.error(f"Error getting analysis from assistant: {str(e)}")
        raise

def preprocess_json(json_string):
    # Remove any leading/trailing whitespace
    json_string = json_string.strip()
    
    # Add missing commas between key-value pairs
    json_string = re.sub(r'"\s*\n\s*"', '",\n"', json_string)
    
    return json_string

def parse_ai_response(response):
    try:
        response = response.strip()
        logging.info(f"Raw AI Response: {response}")

        if not response:
            logging.warning("Received empty response from AI assistant")
            return create_default_analysis()

        # Preprocess the response
        preprocessed_response = preprocess_json(response)
        logging.info(f"Preprocessed AI Response: {preprocessed_response}")

        # Parse the JSON response
        analysis_data = json.loads(preprocessed_response)

        # Validate and fill missing fields
        required_fields = ['key_finding', 'quick_stats', 'interpretation', 'fun_fact']
        for field in required_fields:
            if field not in analysis_data or not analysis_data[field]:
                logging.warning(f"Missing or empty required field: {field}")
                analysis_data[field] = get_default_value(field)

        logging.info("Parsed analysis data successfully")
        return analysis_data

    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON from AI response after preprocessing: {str(e)}")
        return create_default_analysis()
    except Exception as e:
        logging.error(f"Unexpected error processing AI response: {str(e)}")
        return create_default_analysis()

def get_default_value(field):
    defaults = {
        'key_finding': "No key finding available.",
        'quick_stats': ["No specific stats available."],
        'interpretation': "Unable to interpret the results at this time.",
        'fun_fact': "Every survey tells a unique story!"
    }
    return defaults.get(field, "Information not available.")

def create_default_analysis():
    return {
        'key_finding': "Survey results are inconclusive.",
        'quick_stats': ["No specific stats available."],
        'interpretation': "Unable to interpret the results at this time.",
        'fun_fact': "Did you know? Surveys can sometimes be unpredictable!"
    }

def main(user_id, session_id):
    try:
        survey_data = load_survey_data(user_id, session_id)
        analysis_prompt = format_analysis_prompt(survey_data)
        ai_response = get_analysis_from_assistant(analysis_prompt)
        analysis_data = parse_ai_response(ai_response)
        
        # Always save analysis to database, even if it's the default analysis
        SurveyData.save_data(user_id=user_id, session_id=session_id, data_type='survey_analysis', content=analysis_data)
        logging.info(f"Analysis complete. Results saved to database for user {user_id}, session {session_id}")
        
        return analysis_data
    except Exception as e:
        logging.error(f"An error occurred in the main function: {str(e)}")
        default_analysis = create_default_analysis()
        SurveyData.save_data(user_id=user_id, session_id=session_id, data_type='survey_analysis', content=default_analysis)
        logging.info(f"Default analysis saved to database for user {user_id}, session {session_id}")
        return default_analysis

if __name__ == "__main__":
    # This block is for testing purposes and won't be used when called from routes.py
    test_user_id = "test_user"
    test_session_id = "test_session"
    result = main(test_user_id, test_session_id)
    print(json.dumps(result, indent=2))