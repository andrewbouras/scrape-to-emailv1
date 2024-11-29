# app.py
import logging
from flask import Flask
from main import StudyManager
from config import Config
from models import db_manager
from test_clinicaltrials_fetch import test_bp
from dotenv import load_dotenv
import os

def create_app(config_class=Config):
    """Application factory function"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Load environment variables
    load_dotenv()
    
    # Configure the app
    app.config['MONGODB_URI'] = os.getenv('MONGODB_URI')
    app.config['AZURE_OPENAI_KEY'] = os.getenv('AZURE_OPENAI_KEY')
    app.config['AZURE_OPENAI_ENDPOINT'] = os.getenv('AZURE_OPENAI_ENDPOINT')
    app.config['AZURE_OPENAI_VERSION'] = os.getenv('AZURE_OPENAI_VERSION')
    app.config['AZURE_OPENAI_DEPLOYMENT'] = os.getenv('AZURE_OPENAI_DEPLOYMENT')

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Initialize database
    try:
        db_manager.setup_database()
    except Exception as e:
        app.logger.error(f"Failed to setup database: {str(e)}")
        raise

    # Initialize extensions
    study_manager = StudyManager(app.config)
    
    # Register CLI commands
    @app.cli.command('update-studies')
    def update_studies():
        """Update clinical studies data from ClinicalTrials.gov"""
        try:
            app.logger.info("Starting clinical studies update...")
            study_manager.fetch_and_store_data()
            app.logger.info("Clinical studies update completed successfully")
        except Exception as e:
            app.logger.error(f"Failed to update studies: {str(e)}", exc_info=True)
            raise

    # Register blueprints
    app.register_blueprint(test_bp, url_prefix='/test')

    return app

# Create application instance
app = create_app()

if __name__ == '__main__':
    # Changed port from 5000 to 8080
    app.run(host='0.0.0.0', port=8080, debug=True)