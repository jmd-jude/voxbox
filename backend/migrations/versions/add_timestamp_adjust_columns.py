"""Add timestamp and adjust columns

Revision ID: add_timestamp_adjust_columns
Revises: c0d965345b33
Create Date: 2024-09-26 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_timestamp_adjust_columns'
down_revision = 'c0d965345b33'
branch_labels = None
depends_on = None


def upgrade():
    # Create new table
    op.execute('''
        CREATE TABLE new_survey_data (
            id INTEGER NOT NULL PRIMARY KEY,
            user_id VARCHAR(64) NOT NULL,
            session_id VARCHAR(64),
            data_type VARCHAR(50) NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME
        )
    ''')
    
    # Copy data from old table to new table
    op.execute('''
        INSERT INTO new_survey_data (id, user_id, session_id, data_type, content)
        SELECT id, COALESCE(user_id, 'default_user_id'), session_id, data_type, content
        FROM survey_data
    ''')
    
    # Drop old table
    op.execute('DROP TABLE survey_data')
    
    # Rename new table to old table name
    op.execute('ALTER TABLE new_survey_data RENAME TO survey_data')

def downgrade():
    # Create old table structure
    op.execute('''
        CREATE TABLE old_survey_data (
            id INTEGER NOT NULL PRIMARY KEY,
            user_id VARCHAR(64),
            session_id VARCHAR(64) NOT NULL,
            data_type VARCHAR(50) NOT NULL,
            content TEXT NOT NULL
        )
    ''')
    
    # Copy data back, excluding the timestamp column
    op.execute('''
        INSERT INTO old_survey_data (id, user_id, session_id, data_type, content)
        SELECT id, user_id, COALESCE(session_id, ''), data_type, content
        FROM survey_data
    ''')
    
    # Drop new table
    op.execute('DROP TABLE survey_data')
    
    # Rename old table to original name
    op.execute('ALTER TABLE old_survey_data RENAME TO survey_data')