# app.py
import logging
from flask import Flask
from main import StudyManager
from config import Config
from models import db_manager
from test_clinicaltrials_fetch import test_bp

def create_app(config_class=Config):
    """Application factory function"""
    app = Flask(__name__)
    app.config.from_object(config_class)

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
    app.run(debug=True)