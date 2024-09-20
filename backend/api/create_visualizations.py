import json
import os
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import logging

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("data/visualization_creation.log"),
                        logging.StreamHandler()
                    ])

def load_json_file(filename):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"File not found: {filename}")
        raise
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON in file: {filename}")
        raise

def prepare_data(survey_data, recommendation):
    data_description = recommendation['data'].lower()
    
    if 'by age group' in data_description:
        return prepare_demographic_data(survey_data, 'Age', data_description)
    elif 'distribution' in data_description:
        return prepare_distribution_data(survey_data, data_description)
    elif 'across different demographics' in data_description:
        return prepare_cross_demographic_data(survey_data, data_description)
    else:
        return prepare_general_data(survey_data, data_description)

def prepare_demographic_data(survey_data, demographic, description):
    relevant_question = find_relevant_question(survey_data, description)
    if not relevant_question:
        logging.warning(f"No relevant question found for description: {description}")
        return None

    age_groups = {'18-30': (18, 30), '31-50': (31, 50), '51-70': (51, 70), '70+': (71, 120)}
    data = {group: 0 for group in age_groups}
    total = {group: 0 for group in age_groups}

    for response in survey_data['individual_responses']:
        age = response['demographics']['Age']
        group = next((g for g, (low, high) in age_groups.items() if low <= age <= high), None)
        if group:
            total[group] += 1
            if response['responses'].get(relevant_question['question'].split(')')[0].strip(), '').lower() == 'top priority':
                data[group] += 1

    for group in data:
        data[group] = (data[group] / total[group] * 100) if total[group] > 0 else 0

    return data

def prepare_distribution_data(survey_data, description):
    relevant_question = find_relevant_question(survey_data, description)
    if not relevant_question:
        logging.warning(f"No relevant question found for description: {description}")
        return None

    return {answer['text']: answer['percentage'] for answer in relevant_question['answers'] if answer['text'] != 'No answer'}

def prepare_cross_demographic_data(survey_data, description):
    demographics = ['Income', 'Education', 'GeographicRegion']
    priorities = [q['question'].split(')')[1].strip() for q in survey_data['aggregate_results'][:5]]  # Assume first 5 questions are priorities

    data = {demo: {priority: {} for priority in priorities} for demo in demographics}

    for response in survey_data['individual_responses']:
        for demo in demographics:
            demo_value = response['demographics'][demo]
            for i, priority in enumerate(priorities, 1):
                if response['responses'].get(f'Q{i}', '').lower() == 'top priority':
                    data[demo][priority][demo_value] = data[demo][priority].get(demo_value, 0) + 1

    return data

def prepare_general_data(survey_data, description):
    relevant_question = find_relevant_question(survey_data, description)
    if not relevant_question:
        logging.warning(f"No relevant question found for description: {description}")
        return None

    return {answer['text']: answer['percentage'] for answer in relevant_question['answers']}

def find_relevant_question(survey_data, description):
    return next((q for q in survey_data['aggregate_results'] if any(keyword in q['question'].lower() for keyword in description.split())), None)

def create_visualization(data, recommendation):
    chart_type = recommendation['type'].lower()

    if 'bar' in chart_type:
        fig = go.Figure(data=[go.Bar(x=list(data.keys()), y=list(data.values()))])
    elif 'pie' in chart_type:
        fig = go.Figure(data=[go.Pie(labels=list(data.keys()), values=list(data.values()))])
    elif 'stacked' in chart_type:
        fig = create_stacked_bar(data)
    else:
        logging.warning(f"Unrecognized chart type: {chart_type}. Defaulting to bar chart.")
        fig = go.Figure(data=[go.Bar(x=list(data.keys()), y=list(data.values()))])

    fig.update_layout(title=recommendation['purpose'])
    return fig

def create_stacked_bar(data):
    fig = go.Figure()
    for demo, priorities in data.items():
        for priority, values in priorities.items():
            fig.add_trace(go.Bar(
                x=list(values.keys()),
                y=list(values.values()),
                name=f"{demo} - {priority}"
            ))
    fig.update_layout(barmode='stack')
    return fig

def save_visualization(fig, index):
    try:
        if not os.path.exists('data/visualizations'):
            os.makedirs('data/visualizations')
        filename = f"data/visualizations/visualization_{index+1}.html"
        fig.write_html(filename)
        logging.info(f"Saved {filename}")
    except Exception as e:
        logging.error(f"Error saving visualization: {str(e)}")
        raise

def main():
    try:
        survey_data = load_json_file('data/survey_results.json')
        recommendations = load_json_file('data/visualization_recommendations.json')

        for i, recommendation in enumerate(recommendations['visualizations']):
            logging.info(f"Processing visualization {i+1}...")
            data = prepare_data(survey_data, recommendation)
            if data:
                fig = create_visualization(data, recommendation)
                save_visualization(fig, i)
            else:
                logging.warning(f"Could not prepare data for visualization {i+1}")

        logging.info("All visualizations have been created and saved.")
    except Exception as e:
        logging.error(f"An error occurred during visualization creation: {str(e)}")

if __name__ == "__main__":
    main()