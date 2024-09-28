import os
import logging
from flask import Flask
from flask_cors import CORS
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask.cli import with_appcontext
import click
from .config import Config

db = SQLAlchemy()
migrate = Migrate()
logger = logging.getLogger('voxbox')

def create_app():
    logger.info("Starting create_app()")
    # Get the absolute path of the current file (__init__.py)
    base_dir = os.path.abspath(os.path.dirname(__file__))
    # Create the Flask app
    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, '..', '..', 'templates'),
        static_folder=os.path.join(base_dir, '..', '..', 'static'),
        static_url_path=''
    )
    # Load the app configurations
    app.config.from_object(Config)
    Config.init_app(app)
    # Initialize SQLAlchemy with the app
    db.init_app(app)
    # Initialize Flask-Migrate
    migrate.init_app(app, db)
    # Initialize CORS and session
    CORS(app)
    Session(app)
    logger.info("CORS and Session initialized")
    # Log the template and static folder paths for debugging
    logger.info(f"Template folder path: {app.template_folder}")
    logger.info(f"Static folder path: {app.static_folder}")
    # Register routes
    with app.app_context():
        logger.info("Registering routes")
        from .routes import main
        app.register_blueprint(main)
        logger.info("Routes registered")
        # Import models to ensure they are loaded into SQLAlchemy
        from .models import SurveyData
        logger.info("SurveyData model loaded")
    # Register the init-db command
    init_app(app)
    logger.info("Returning app instance")
    return app

@click.command('init-db')
@with_appcontext
def init_db_command():
    # Ensure models are loaded
    from .models import SurveyData
    db.create_all()
    click.echo('Initialized the database.')
    logger.info("SurveyData table created")

def init_app(app):
    app.cli.add_command(init_db_command)