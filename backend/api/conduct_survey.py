import pandas as pd
import numpy as np
import random
import logging
import json
from typing import List, Dict, Any
from .config import Config
from .models import SurveyData
import os

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Ensure reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

def load_data() -> pd.DataFrame:
    try:
        file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'american_profiles_2024.json')
        with open(file_path, 'r') as file:
            profiles_data = json.load(file)
        profiles_df = pd.DataFrame(profiles_data)
        logging.info("Data loaded successfully")
        return profiles_df
    except Exception as e:
        logging.error(f"Error loading data: {str(e)}")
        raise

def load_approved_question(user_id, session_id):
    try:
        question_data = SurveyData.get_data(session_id, 'transformed_question', user_id)
        if not question_data:
            raise ValueError("No approved question found for this user and session")
        return question_data
    except Exception as e:
        logging.error(f"Error loading latest question: {str(e)}")
        raise

def simulate_response(row: pd.Series, question: Dict[str, Any]) -> str:
    options = question.get('options', {})
    
    if isinstance(options, dict):
        option_list = list(options.values())
    elif isinstance(options, list):
        option_list = options
    else:
        logging.error(f"Unexpected options type: {type(options)}")
        return "Error: Invalid options"
    
    if not option_list:
        logging.error("No valid options found in the question")
        return "No Answer"
    
    weights = [1/len(option_list)] * len(option_list)  # Equal weights for simplicity
    
    # Log options and weights only once at DEBUG level
    logging.debug(f"Options: {options}")
    logging.debug(f"Weights: {weights}")
    
    try:
        return random.choices(option_list, weights=weights)[0]
    except Exception as e:
        logging.error(f"Error in simulate_response: {str(e)}")
        logging.error(f"Question structure: {question}")
        return "Error"

def calculate_weighted_results(responses: List[Dict[str, Any]], question: Dict[str, Any]) -> Dict[str, Any]:
    weighted_responses = {}
    total_weight = 0
    
    for response in responses:
        answer = response['response']
        weight = response['weight']
        weighted_responses[answer] = weighted_responses.get(answer, 0) + weight
        total_weight += weight
    
    percentages = {k: (v / total_weight * 100) for k, v in weighted_responses.items()}
    options = question.get('options', {})
    
    if isinstance(options, dict):
        answer_mapping = {v: k for k, v in options.items()}
    else:
        answer_mapping = {opt: opt for opt in options}
    
    result = {
        'question': question['question'],
        'type': question['type'],
        'answers': [{'text': k, 'label': answer_mapping.get(k, k), 'percentage': v} for k, v in percentages.items()]
    }
    
    return result

def conduct_single_question_survey(user_id, session_id, num_respondents=None):
    if num_respondents is None:
        num_respondents = Config.NUM_SURVEY_RESPONDENTS
    
    try:
        # Load necessary data
        profiles_df = load_data()
        latest_question = load_approved_question(user_id, session_id)
        question_config = SurveyData.get_data(session_id, 'question_config', user_id)
        
        if not question_config:
            raise ValueError("No question config found for this user and session")
        
        # Prepare survey data
        survey_data = profiles_df.sample(n=num_respondents, replace=True).reset_index(drop=True)
        
        # Simulate responses
        responses = []
        for _, row in survey_data.iterrows():
            response = simulate_response(row, latest_question)
            responses.append({
                "demographics": row.to_dict(),
                "response": response,
                "weight": 1  # need to create and implement calculate_weight function
            })
        
        # Calculate results
        results = calculate_weighted_results(responses, latest_question)
        
        # Prepare the full results dictionary
        full_results = {
            "aggregate_results": results,
            "individual_responses": responses
        }
        
        # Save results to database
        SurveyData.save_data(user_id=user_id, session_id=session_id, data_type='survey_results', content=full_results)
        logging.info(f"Survey results saved to database for user {user_id}, session {session_id}")
        return full_results
    except Exception as e:
        logging.error(f"Error in conduct_single_question_survey: {str(e)}")
        raise