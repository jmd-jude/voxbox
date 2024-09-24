from flask import Blueprint, jsonify, request, session, render_template
from . import create_survey, conduct_survey, create_survey_analysis
from .create_survey_analysis import parse_ai_response
from .config import Config
import subprocess
import os
import json
import logging

# Set up logging
logging.basicConfig(filename='app.log', level=logging.INFO, 
                    format='%(asctime)s %(levelname)s: %(message)s')

main = Blueprint('main', __name__)

def generate_poll_config_from_file():
    try:
        # Run the create_question_config.py script
        script_path = os.path.join(os.getcwd(), 'api', 'create_question_config.py')
        result = subprocess.run(['python3', script_path], capture_output=True, text=True)
        
        if result.returncode != 0:
            logging.error(f"Error running create_question_config.py: {result.stderr}")
            raise Exception("Failed to generate poll config")

        # Read the generated question_config.json
        config_path = os.path.join(os.getcwd(), 'data', 'question_config.json')
        with open(config_path, 'r') as f:
            question_config = json.load(f)

        return question_config

    except Exception as e:
        logging.error(f"Error in generate_poll_config_from_file: {str(e)}", exc_info=True)
        raise

@main.route('/')
def home():
    print("Rendering index.html")
    return render_template('index.html')

@main.route('/transform-question', methods=['POST'])
def transform_question_route():
    logging.info("Entered transform_question_route")
    try:
        user_question = request.json.get('question', None)
        
        if not user_question:
            logging.warning("No question received")
            return jsonify({"error": "No question provided"}), 400
        
        logging.info(f"Received question: {user_question}")
        logging.info("Calling transform_question function")
        
        # Transform the question
        transformed_question = create_survey.transform_question(user_question)
        logging.info(f"Transformed question: {transformed_question}")
        
        # Store the original and transformed question in the session
        session['last_question'] = user_question
        session['last_transformed_question'] = transformed_question
        session.modified = True  # This ensures the session is saved

        logging.info(f"Session after transform: {session}")
        
        return jsonify({
            "original_question": user_question,
            "transformed_question": transformed_question
        })
    
    except Exception as e:
        logging.error(f"Error in transform_question_route: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to transform question"}), 500

from flask import session

@main.route('/approve-question', methods=['POST'])
def approve_question_route():
    logging.info("Entered approve_question_route")
    try:
        approved = request.json.get('approved', False)
        
        if approved:
            # Retrieve the last transformed question from the session
            transformed_question = session.get('last_transformed_question')
            original_question = session.get('last_question')
            
            logging.info(f"Retrieved from session - transformed: {transformed_question}, original: {original_question}")
            
            if not transformed_question or not original_question:
                logging.warning("No transformed question or original question found in session")
                return jsonify({"error": "No question found in session. Please submit a question first."}), 400

            # Generate session-specific filenames
            session_id = session.sid
            approved_question_filename = f"approved_question_{session_id}.json"
            survey_results_filename = f"survey_results_{session_id}.json"
            analysis_filename = f"survey_analysis_{session_id}.json"
            
            approved_question_path = os.path.join('data', approved_question_filename)
            survey_results_path = os.path.join('data', survey_results_filename)
            analysis_path = os.path.join('data', analysis_filename)

            # Save the approved question to file
            with open(approved_question_path, 'w') as f:
                json.dump({"original": original_question, "transformed": transformed_question}, f, indent=2)
            
            logging.info(f"Saved approved question to {approved_question_path}")

            # Conduct survey
            survey_results = conduct_survey.conduct_single_question_survey(session_id)
            
            # Save survey results
            with open(survey_results_path, 'w') as f:
                json.dump(survey_results, f, indent=2)
            
            logging.info(f"Saved survey results to {survey_results_path}")

            # Generate and get analysis
            analysis_result = create_survey_analysis.main(
                approved_question_path,
                survey_results_path,
                analysis_path
            )

            logging.info(f"Approved question: {transformed_question}")
            
            # Clear session data after successfully processing
            session.pop('last_question', None)
            session.pop('last_transformed_question', None)
            session.modified = True
            
            return jsonify({
                "approved_question": transformed_question,
                "survey_results": survey_results,
                "analysis": analysis_result
            })
        
        else:
            # If the question was not approved, return an appropriate response
            logging.info("User did not approve. Re-transforming question...")
            user_question = session.get('last_question')
            
            if not user_question:
                logging.warning("No original question found in session to retry transformation")
                return jsonify({"error": "No original question found to retry"}), 400
            
            logging.info("Calling transform_question function again")
            transformed_question = create_survey.transform_question(user_question)
            session['last_transformed_question'] = transformed_question
            session.modified = True
            
            return jsonify({
                "message": "Got it! We're trying again!",
                "new_transformed_question": transformed_question
            })
    
    except Exception as e:
        logging.error(f"Error in approve_question_route: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to process approved question"}), 500

@main.route('/conduct-survey', methods=['POST'])
def run_survey():
    logging.info("Entered run_survey route")
    try:
        result = conduct_survey.conduct_single_question_survey()
        
        # Generate session-specific filename
        session_id = session.sid
        filename = f"survey_results_{session_id}.json"
        file_path = os.path.join('data', filename)
        
        # Save survey results with session-specific filename
        with open(file_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        logging.info(f"Survey conducted successfully. Results saved to {file_path}")
        
        return jsonify({"result": result})
    except Exception as e:
        logging.error(f"Error conducting survey: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to conduct survey"}), 500

@main.route('/create-analysis', methods=['POST'])
def create_analysis_route():
    logging.info("Entered create_analysis_route")
    try:
        # Generate session-specific filenames
        session_id = session.sid
        approved_question_filename = f"approved_question_{session_id}.json"
        survey_results_filename = f"survey_results_{session_id}.json"
        analysis_filename = f"survey_analysis_{session_id}.json"
        
        approved_question_path = os.path.join('data', approved_question_filename)
        survey_results_path = os.path.join('data', survey_results_filename)
        analysis_path = os.path.join('data', analysis_filename)

        # Call the analysis function with session-specific file paths
        analysis_data = create_survey_analysis.main(approved_question_path, survey_results_path, analysis_path)

        logging.info(f"Analysis created successfully. Saved to {analysis_path}")
        return jsonify(analysis_data)
    except FileNotFoundError as e:
        logging.error(f"File not found: {str(e)}")
        return jsonify({"error": f"File not found: {str(e)}"}), 404
    except json.JSONDecodeError:
        logging.error("Invalid JSON in analysis data")
        return jsonify({"error": "Invalid JSON in analysis data"}), 400
    except Exception as e:
        logging.error(f"Error in create_analysis_route: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500