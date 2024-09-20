import os
import json
import time
import logging
import re
import openai
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("data/survey_analysis.log"),
                        logging.StreamHandler()
                    ])

# Load environment variables
load_dotenv()

# Set up OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

ASSISTANT_ID = "asst_GEqxbSSDWkKNAcxWdWJqMhYd"

def load_survey_data():
    try:
        with open('data/approved_question.json', 'r') as f:
            question_data = json.load(f)
        with open('data/survey_results.json', 'r') as f:
            results = json.load(f)
        
        logging.info("Loaded survey data: "
                     "Question: %s, "
                     "Aggregate results: %d, "
                     "Individual responses: %d",
                     question_data['transformed']['question'],
                     len(results['aggregate_results']['answers']),
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

    Please provide a concise analysis in the following format:

    1. Key Finding: A one-sentence summary of the most important insight.

    2. Quick Stats: Three interesting statistics from the results.

    3. Interpretation: Two short paragraphs explaining what these results mean and their potential implications.

    4. Fun Fact: An interesting or surprising fact from the data.

    After your analysis, include the following delimiter: [END_ANALYSIS]

    Then, provide exactly 2 visualization recommendations in this JSON format:

    {{
      "visualizations": [
        {{
          "type": "[chart type]",
          "title": "[brief title for the chart]",
          "description": "[what this visualization will show]"
        }},
        {{
          "type": "[chart type]",
          "title": "[brief title for the chart]",
          "description": "[what this visualization will show]"
        }}
      ]
    }}

    Ensure your response includes both the analysis (ending with [END_ANALYSIS]) and the visualization recommendations in the specified JSON format.
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
        
        # Log the full response
        logging.info("Full response from assistant:")
        logging.info(response)
        
        return response
    except Exception as e:
        logging.error(f"Error getting analysis from assistant: {str(e)}")
        raise

def parse_ai_response(response):
    try:
        # If the response is already a dictionary, return it
        if isinstance(response, dict):
            return response['summary'], response['full_analysis']

        # Otherwise, proceed with string parsing
        parts = response.split("[END_ANALYSIS]")
        if len(parts) != 2:
            raise ValueError("Response format is incorrect. Missing [END_ANALYSIS] delimiter.")

        analysis = parts[0].strip()
        viz_part = parts[1].strip()

        # Parse the analysis into sections more flexibly
        sections = analysis.split('\n\n')

        # Ensure all sections have fallback values if missing
        summary = {
            'key_finding': sections[0] if len(sections) > 0 else "No key finding available.",
            'quick_stats': sections[1].strip().split('\n') if len(sections) > 1 else ["No quick stats available."],
            'interpretation': ' '.join(sections[2:4]) if len(sections) > 3 else (sections[2] if len(sections) > 2 else "No interpretation available."),
            'fun_fact': sections[4] if len(sections) > 4 else "No fun fact available."
        }

        logging.info(f"Parsed analysis summary successfully")
        return summary, analysis  # Return summary and analysis

    except json.JSONDecodeError as e:
        logging.error(f"Error parsing visualization JSON: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"Error parsing AI response: {str(e)}")
        raise

def save_narrative_analysis(narrative, file_path):
    try:
        with open(file_path, 'w') as f:
            f.write(narrative)
        logging.info(f"Narrative analysis saved to {file_path}")
    except Exception as e:
        logging.error(f"Error saving narrative analysis: {str(e)}")
        raise

def save_visualization_recommendations(recommendations, file_path):
    try:
        with open(file_path, 'w') as f:
            f.write(recommendations)
        logging.info(f"Visualization recommendations saved to {file_path}")
    except Exception as e:
        logging.error(f"Error saving visualization recommendations: {str(e)}")
        raise

def main():
    try:
        survey_data = load_survey_data()
        analysis_prompt = format_analysis_prompt(survey_data)
        ai_response = get_analysis_from_assistant(analysis_prompt)
        summary, full_analysis, = parse_ai_response(ai_response)

        # Save full analysis to Markdown file
        save_narrative_analysis(full_analysis, 'data/survey_analysis.md')
        
        
        logging.info("Analysis complete. Results saved and returned.")
        return {
            'summary': summary,
            'full_analysis': full_analysis,
        }
    except Exception as e:
        logging.error(f"An error occurred in the main function: {str(e)}")
        raise

if __name__ == "__main__":
    result = main()
    print(json.dumps(result, indent=2))