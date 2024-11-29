# generate.py
from flask import Blueprint, jsonify, current_app
import logging
from api_client import fetch_all_studies
from data_extractor import extract_fields
from storage import DataStorage
from study_processor import StudyProcessor
from config import FIELDS_TO_EXTRACT

gi_bp = Blueprint('gi', __name__)
storage = DataStorage()

@gi_bp.route('/fetch_gi_studies', methods=['GET'])
def fetch_gi_studies():
    try:
        logging.info("Fetching GI studies from ClinicalTrials.gov")
        
        # Get configuration
        config = {
            'AZURE_OPENAI_KEY': current_app.config['AZURE_OPENAI_KEY'],
            'AZURE_OPENAI_ENDPOINT': current_app.config['AZURE_OPENAI_ENDPOINT'],
            'AZURE_OPENAI_VERSION': current_app.config['AZURE_OPENAI_VERSION'],
            'AZURE_OPENAI_DEPLOYMENT': current_app.config['AZURE_OPENAI_DEPLOYMENT']
        }
        
        # Initialize processor
        processor = StudyProcessor(config)
        
        # Fetch and process
        studies = fetch_all_studies(FIELDS_TO_EXTRACT)
        extracted_data = extract_fields(studies)
        processed_data = processor.process_studies(extracted_data)
        
        # Save results
        storage.save_data(processed_data, 'gi_studies.json')
        
        return jsonify({
            "message": "GI studies data fetched and saved successfully",
            "count": len(processed_data)
        }), 200
        
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500