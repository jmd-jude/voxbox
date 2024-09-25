import os
import json
import re
import time
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
ASSISTANT_ID = "asst_GEqxbSSDWkKNAcxWdWJqMhYd"

DEMOGRAPHIC_VARIABLES = {
    "Gender": ["Male", "Female"],
    "Race": ["White", "Black", "Hispanic", "Asian", "Other", "Mixed Race"],
    "Ethnicity": ["White", "Black", "Hispanic or Latino", "Asian", "Other"],
    "Age": ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"],
    "Income": ["$0-$24,999", "$25,000-$49,999", "$50,000-$99,999", "$100,000+"],
    "EmploymentStatus": ["Employed", "Unemployed", "Retired", "Student", "Not in labor force"],
    "Education": ["HS or less", "Some college", "College grad"],
    "HouseholdType": ["Single-parent", "Married-couple", "Other"],
    "HousingStatus": ["Owner", "Renter"],
    "FamilyComposition": ["Single", "Married with children", "Married without children", "Single-parent household"],
    "Urbanicity": ["Urban", "Suburban", "Rural"],
    "HealthStatus": ["Excellent", "Very Good", "Good", "Fair", "Poor"],
    "InternetUsage": ["Daily", "Weekly", "Rarely", "Never"],
    "GeographicRegion": ["Northeast", "Midwest", "South", "West"],
    "PoliticalAffiliation": ["Democrat", "Republican", "Independent", "Other"],
    "ReligiousAffiliation": ["Christian", "Jewish", "Muslim", "Other", "Non-religious"],
    "HealthInsurance": ["Insured", "Uninsured"]
}

# Define the path to the data directory
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')


def read_approved_question(file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        return data.get("transformed", "")
    except Exception as e:
        print(f"Error reading latest question: {str(e)}")
        return ""


def generate_question_config(question):
    prompt = f"""
    As Nate Bronze, the Chief Data Scientist, generate a question_config.json file based on the following survey question. For this question:
    1. Assign four relevant demographic variables from the following list:
    {', '.join(DEMOGRAPHIC_VARIABLES.keys())}
    2. For each demographic variable, provide appropriate categories and their corresponding weights (proportions) that sum to 1.0. Use only the following categories for each variable:
    {json.dumps(DEMOGRAPHIC_VARIABLES, indent=2)}
    Use the following format for the JSON structure:
    {{
    "DemographicVariable1": {{
        "Category1": weight,
        "Category2": weight,
        ...
    }},
    "DemographicVariable2": {{
        "Category1": weight,
        "Category2": weight,
        ...
    }},
    "DemographicVariable3": {{
        "Category1": weight,
        "Category2": weight,
        ...
    }},
    "DemographicVariable4": {{
        "Category1": weight,
        "Category2": weight,
        ...
    }}
    }}
    Ensure that you only use the demographic variables and categories from the provided list. The weights should reflect realistic distributions based on your expertise.
    Survey question:
    {question}
    IMPORTANT: Respond ONLY with the JSON content. Do not include any explanations or additional text before or after the JSON.
    """
    # Create a thread
    thread = client.beta.threads.create()
    # Add a message to the thread
    message = client.beta.threads.messages.create(
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
        time.sleep(1)
    # Retrieve the messages
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    # Get the last message from the assistant
    last_message = messages.data[0]
    return last_message.content[0].text.value


def save_json(data, file_path):
    try:
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', data)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = data
        json_data = json.loads(json_str)
        with open(file_path, 'w') as file:
            json.dump(json_data, file, indent=2)
        print(f"Successfully saved {file_path}")
        return True
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON response. Details: {str(e)}")
        print("Full API Response:")
        print(data)
        return False
    except Exception as e:
        print(f"Unexpected error while saving JSON: {str(e)}")
        return False


def print_first_10_lines(file_path):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
        print(f"\nFirst 10 lines of {file_path}:")
        for line in lines[:10]:
            print(line.strip())
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")


def main():
    try:
        latest_question = read_approved_question(os.path.join(DATA_DIR, 'approved_question.json'))
        if not latest_question:
            raise ValueError("No question found in approved_question.json")
        question_config = generate_question_config(latest_question)
        if save_json(question_config, os.path.join(DATA_DIR, 'question_config.json')):
            print_first_10_lines(os.path.join(DATA_DIR, 'question_config.json'))
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")


if __name__ == "__main__":
    main()