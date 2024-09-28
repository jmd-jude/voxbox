from . import db
import json
import logging
from datetime import datetime
from sqlalchemy import Index

class SurveyData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(64), nullable=True, index=True)
    session_id = db.Column(db.String(64), nullable=False, index=True)
    data_type = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index('idx_session_data_type', 'session_id', 'data_type'),
    )

    @classmethod
    def save_data(cls, user_id, session_id, data_type, content):
        try:
            data = cls(user_id=user_id, session_id=session_id, data_type=data_type, content=json.dumps(content))
            db.session.add(data)
            db.session.commit()
            logging.info(f"Data saved successfully. User ID: {user_id}, Session ID: {session_id}, Type: {data_type}")
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error saving data: {str(e)}")
            raise

    @classmethod
    def get_data(cls, session_id, data_type, user_id=None):
        try:
            query = cls.query.filter_by(session_id=session_id, data_type=data_type)
            if user_id:
                query = query.filter_by(user_id=user_id)
            data = query.order_by(cls.timestamp.desc()).first()
            if data:
                logging.info(f"Data retrieved successfully. User ID: {user_id}, Session ID: {session_id}, Type: {data_type}")
                return json.loads(data.content)
            else:
                logging.warning(f"No data found. User ID: {user_id}, Session ID: {session_id}, Type: {data_type}")
                return None
        except Exception as e:
            logging.error(f"Error retrieving data: {str(e)}")
            return None