from flask import Blueprint, jsonify, request, session, render_template
from . import create_survey, conduct_survey, create_survey_analysis, create_question_config
from .config import Config
import logging
from .models import SurveyData
from . import db
from .session_management import get_user_and_session_ids, update_session_activity, generate_new_session_id, get_or_create_user_id
from flask import send_file
import sqlite3
import csv
import io
import zipfile
import os

# Set up logging
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
main = Blueprint('main', __name__)

@main.before_request
def before_request():
    get_user_and_session_ids()

@main.route('/generate-poll-config', methods=['POST'])
def generate_poll_config():
    logging.info("Entered generate_poll_config route")
    try:
        user_id, session_id = get_user_and_session_ids()
        update_session_activity()
        logging.info(f"[generate_poll_config] User ID: {user_id}, Session ID: {session_id}")
        create_question_config.main(user_id, session_id)
        question_config = SurveyData.get_data(session_id, 'question_config', user_id)
        if not question_config:
            raise ValueError("Failed to generate question config")
        logging.info(f"Poll config generated successfully for user {user_id}, session {session_id}")
        return jsonify({"config": question_config})
    except Exception as e:
        logging.error(f"Error in generate_poll_config: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to generate poll config"}), 500

@main.route('/')
def home():
    logging.info("Rendering index.html")
    return render_template('index.html')

@main.route('/transform-question', methods=['POST'])
def transform_question_route():
    logging.info("Entered transform_question_route")
    try:
        user_id, session_id = get_user_and_session_ids()
        update_session_activity()
        user_question = request.json.get('question', None)
        if not user_question:
            logging.warning("No question received")
            return jsonify({"error": "No question provided"}), 400
        logging.info(f"Received question for user {user_id}, session {session_id}: {user_question}")
        logging.info("Calling process_and_save_question function")
        transformed_question = create_survey.process_and_save_question(user_id, session_id, user_question)
        logging.info(f"Transformed question: {transformed_question}")
        SurveyData.save_data(user_id=user_id, session_id=session_id, data_type='transformed_question', content=transformed_question)
        SurveyData.save_data(user_id=user_id, session_id=session_id, data_type='original_question', content=user_question)
        logging.info(f"Transformed question saved to database for user {user_id}, session {session_id}")
        return jsonify({
            "original_question": user_question,
            "transformed_question": transformed_question
        })
    except Exception as e:
        logging.error(f"Error in transform_question_route: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to transform question"}), 500

@main.route('/approve-question', methods=['POST'])
def approve_question_route():
    logging.info("Entered approve_question_route")
    try:
        user_id, session_id = get_user_and_session_ids()
        update_session_activity()
        approved = request.json.get('approved', False)
        logging.info(f"User ID: {user_id}, Session ID: {session_id}, Approved: {approved}")

        if approved:
            transformed_question = SurveyData.get_data(session_id, 'transformed_question', user_id)
            original_question = SurveyData.get_data(session_id, 'original_question', user_id)
            logging.info(f"Retrieved from database - transformed: {transformed_question}, original: {original_question}")

            if not transformed_question or not original_question:
                logging.warning(f"No question found in database for user {user_id}, session {session_id}")
                return jsonify({"error": "No question found in database. Please submit a question first."}), 400

            create_question_config.main(user_id, session_id)
            question_config = SurveyData.get_data(session_id, 'question_config', user_id)
            if not question_config:
                logging.warning("Failed to generate question config")
                question_config = {"error": "Failed to generate question config"}

            survey_results = conduct_survey.conduct_single_question_survey(user_id, session_id)
            SurveyData.save_data(user_id=user_id, session_id=session_id, data_type='survey_results', content=survey_results)
            logging.info(f"Saved survey results to database for user {user_id}, session {session_id}")

            analysis_result = create_survey_analysis.main(user_id, session_id)
            if not analysis_result:
                logging.warning("Failed to generate analysis")
                analysis_result = create_survey_analysis.create_default_analysis()

            logging.info(f"Approved question for user {user_id}, session {session_id}: {transformed_question}")
            return jsonify({
                "approved_question": transformed_question,
                "question_config": question_config,
                "survey_results": survey_results,
                "analysis": analysis_result
            })

        else:
            logging.info(f"User {user_id}, session {session_id} did not approve. Re-transforming question...")
            original_question = SurveyData.get_data(session_id, 'original_question', user_id)
            if not original_question:
                logging.warning(f"No original question found in database for user {user_id}, session {session_id} to retry transformation")
                return jsonify({"error": "No original question found to retry"}), 400

            logging.info("Calling transform_question function again")
            transformed_question = create_survey.transform_question(original_question)
            SurveyData.save_data(user_id=user_id, session_id=session_id, data_type='transformed_question', content=transformed_question)
            return jsonify({
                "message": "Got it! We're trying again!",
                "new_transformed_question": transformed_question
            })

    except Exception as e:
        logging.error(f"Error in approve_question_route: {str(e)}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred. Please try again."}), 500

@main.route('/conduct-survey', methods=['POST'])
def run_survey():
    logging.info("Entered run_survey route")
    try:
        user_id, session_id = get_user_and_session_ids()
        update_session_activity()
        logging.info(f"[run_survey] User ID: {user_id}, Session ID: {session_id}")
        result = conduct_survey.conduct_single_question_survey(user_id, session_id)
        SurveyData.save_data(user_id=user_id, session_id=session_id, data_type='survey_results', content=result)
        logging.info(f"Survey conducted successfully. Results saved to database for user {user_id}, session {session_id}")
        return jsonify({"result": result})
    except Exception as e:
        logging.error(f"Error conducting survey: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to conduct survey"}), 500

@main.route('/create-analysis', methods=['POST'])
def create_analysis_route():
    logging.info("Entered create_analysis_route")
    try:
        user_id, session_id = get_user_and_session_ids()
        update_session_activity()
        logging.info(f"[create_analysis_route] User ID: {user_id}, Session ID: {session_id}")
        analysis_data = create_survey_analysis.main(user_id, session_id)
        logging.info(f"Analysis created successfully for user {user_id}, session {session_id}")
        SurveyData.save_data(user_id=user_id, session_id=session_id, data_type='survey_analysis', content=analysis_data)
        logging.info(f"Analysis saved to database for user {user_id}, session {session_id}")
        return jsonify(analysis_data)
    except Exception as e:
        logging.error(f"Error in create_analysis_route: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@main.route('/init-db')
def init_db():
    db.create_all()
    return "Database initialized"

@main.route('/start-new-survey', methods=['POST'])
def start_new_survey():
    logging.info("Starting a new survey")
    try:
        user_id = get_or_create_user_id()
        new_session_id = generate_new_session_id()
        logging.info(f"New survey started for user {user_id}, New Session ID: {new_session_id}")
        # You might want to reset some other session data here if needed
        return jsonify({"message": "New survey started", "session_id": new_session_id})
    except Exception as e:
        logging.error(f"Error starting new survey: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to start new survey"}), 500
    
@main.route('/export-data', methods=['GET'])
def export_data():
    db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'app.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get list of all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    # Create a ZIP file in memory
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for table in tables:
            table_name = table[0]
            # Query all data from the table
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()

            # Create a CSV in memory
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write out column names
            writer.writerow([description[0] for description in cursor.description])
            
            # Write data rows
            writer.writerows(rows)

            # Add CSV to ZIP
            zf.writestr(f"{table_name}.csv", output.getvalue())

    # Close the database connection
    conn.close()

    # Prepare ZIP file for sending
    memory_file.seek(0)
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        attachment_filename='exported_data.zip'
    )