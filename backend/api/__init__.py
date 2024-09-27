import os
from flask import Flask
from flask_cors import CORS
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask.cli import with_appcontext
import click
from .config import Config

db = SQLAlchemy()

def create_app():
    print("Starting create_app()")
    # Get the absolute path of the current file (__init__.py)
    base_dir = os.path.abspath(os.path.dirname(__file__))
    # Create the Flask app
    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, 'templates'),
        static_folder=os.path.join(base_dir, 'static'),
        static_url_path=''
    )
    # Load the app configurations
    app.config.from_object(Config)
    Config.init_app(app)
    # Initialize SQLAlchemy with the app
    db.init_app(app)
    # Initialize CORS and session
    CORS(app)
    Session(app)
    print("CORS and Session initialized")
    # Print out the template and static folder paths for debugging
    print("Template folder path:", app.template_folder)
    print("Static folder path:", app.static_folder)
    # Register routes
    with app.app_context():
        print("Registering routes")
        from .routes import main
        app.register_blueprint(main)
        print("Routes registered")
        # Import models to ensure they are loaded into SQLAlchemy
        from .models import SurveyData
        print("SurveyData model loaded")
    # Register the init-db command
    init_app(app)
    print("Returning app instance")
    return app

@click.command('init-db')
@with_appcontext
def init_db_command():
    # Ensure models are loaded
    from .models import SurveyData
    db.create_all()
    click.echo('Initialized the database.')
    print("SurveyData table created")

def init_app(app):
    app.cli.add_command(init_db_command)