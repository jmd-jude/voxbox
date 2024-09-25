import os
from flask import Flask
from flask_cors import CORS
from flask_session import Session
from .config import Config

def create_app():
    print("Starting create_app()")
    
    # Get the absolute path of the current file (__init__.py)
    base_dir = os.path.abspath(os.path.dirname(__file__))
    
    # Create the Flask app
    app = Flask(__name__,
                template_folder=os.path.join(base_dir, 'templates'),
                static_folder=os.path.join(base_dir, 'static'),
                static_url_path='')
    
    # Print out the template and static folder paths for debugging
    print("Template folder path:", app.template_folder)
    print("Static folder path:", app.static_folder)

    # Load the app configurations
    app.config.from_object(Config)
    Config.init_app(app)

    # Initialize CORS and session
    CORS(app)
    Session(app)
    print("CORS and Session initialized")
    
    # Register routes
    with app.app_context():
        print("Registering routes")
        from .routes import main
        app.register_blueprint(main)
        print("Routes registered")

    print("Returning app instance")
    return app