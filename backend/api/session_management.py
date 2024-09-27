import uuid
from datetime import datetime, timedelta
from flask import session

SESSION_TIMEOUT = timedelta(minutes=30)

def generate_id():
    return str(uuid.uuid4())

def get_or_create_user_id():
    if 'user_id' not in session:
        session['user_id'] = generate_id()
    return session['user_id']

def generate_new_session_id():
    session['session_id'] = generate_id()
    session['last_activity'] = datetime.utcnow()
    return session['session_id']

def get_or_create_session_id():
    current_time = datetime.utcnow()
    if 'session_id' not in session or 'last_activity' not in session:
        session['session_id'] = generate_id()
        session['last_activity'] = current_time
    elif current_time - session['last_activity'] > SESSION_TIMEOUT:
        session['session_id'] = generate_id()
        session['last_activity'] = current_time
    return session['session_id']

def update_session_activity():
    session['last_activity'] = datetime.utcnow()

def get_user_and_session_ids():
    user_id = get_or_create_user_id()
    session_id = get_or_create_session_id()
    update_session_activity()
    return user_id, session_id