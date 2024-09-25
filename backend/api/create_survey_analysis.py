import os
import json
import time
import logging
import openai
from dotenv import load_dotenv
from .config import Config

# Set up logging
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(os.path.join(DATA_DIR, "survey_analysis.log")),
                        logging.StreamHandler()
                    ])

# Load environment variables
load_dotenv()

# Set up OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
ASSISTANT_ID = Config.ASSISTANTS["survey_analyst"]

def load_survey_data(approved_question_path, survey_results_path):
    try:
        with open(approved_question_path, 'r') as f:
            question_data = json.load(f)
        with open(survey_results_path, 'r') as f:
            results = json.load(f)
        logging.info("Loaded survey data: "
                     "Question: %s, "
                     "Aggregate results: %d, "
                     "Individual responses: %d",
                     question_data['transformed']['question'],
                     len(results["aggregate_results"]['answers']),
                     len(results['individual_responses']))
        return {
            'question': question_data['transformed'],
            'aggregate_results': results['aggregate_results'],
            'individual_responses': results['individual_responses']
        }
    except FileNotFoundError as e:
        logging.error(f"File not found: {e.filename}")
        raise
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error loading survey data: {str(e)}")
        raise

def format_analysis_prompt(survey_data):
    prompt = f"""
    Analyze the following survey data and provide a brief, engaging summary:
    Question: {survey_data['question']['question']}
    Aggregate Results:
    {json.dumps(survey_data['aggregate_results'], indent=2)}
    Please provide a concise analysis in the following JSON format:
    {{
        "key_finding": "A one-sentence summary of the most important insight.",
        "quick_stats": [
            "First interesting statistic from the results.",
            "Second interesting statistic from the results.",
            "Third interesting statistic from the results."
        ],
        "interpretation": "Two short paragraphs explaining what these results mean and their potential implications.",
        "fun_fact": "An interesting or surprising fact from the data."
    }}
    Ensure your response is a valid JSON object containing all the specified fields.
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
        logging.info("Analysis received from assistant.")
        return response
    except Exception as e:
        logging.error(f"Error getting analysis from assistant: {str(e)}")
        raise

def parse_ai_response(response):
    try:
        analysis_data = json.loads(response)
        # Validate that all required fields are present
        required_fields = ['key_finding', 'quick_stats', 'interpretation', 'fun_fact']
        for field in required_fields:
            if field not in analysis_data:
                raise ValueError(f"Missing required field: {field}")
        logging.info("Parsed analysis data successfully")
        return analysis_data
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing AI response JSON: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"Error processing AI response: {str(e)}")
        raise

def save_analysis(analysis_data, file_path):
    try:
        with open(file_path, 'w') as f:
            json.dump(analysis_data, f, indent=2)
        logging.info(f"Analysis saved to {file_path}")
    except Exception as e:
        logging.error(f"Error saving analysis: {str(e)}")
        raise

def main(approved_question_path, survey_results_path, analysis_output_path):
    try:
        survey_data = load_survey_data(approved_question_path, survey_results_path)
        analysis_prompt = format_analysis_prompt(survey_data)
        ai_response = get_analysis_from_assistant(analysis_prompt)
        analysis_data = parse_ai_response(ai_response)
        # Save analysis to JSON file
        save_analysis(analysis_data, analysis_output_path)
        logging.info("Analysis complete. Results saved and returned.")
        return analysis_data
    except Exception as e:
        logging.error(f"An error occurred in the main function: {str(e)}")
        raise

if __name__ == "__main__":
    # This block is for testing purposes and won't be used when called from routes.py
    session_id = "test_session"
    approved_question_path = os.path.join(DATA_DIR, f'approved_question_{session_id}.json')
    survey_results_path = os.path.join(DATA_DIR, f'survey_results_{session_id}.json')
    analysis_output_path = os.path.join(DATA_DIR, f'survey_analysis_{session_id}.json')
    result = main(approved_question_path, survey_results_path, analysis_output_path)
    print(json.dumps(result, indent=2))