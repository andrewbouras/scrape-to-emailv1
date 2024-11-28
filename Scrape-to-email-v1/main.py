import logging
from api_client import fetch_all_studies
from data_extractor import extract_fields
from email_generator import generate_email_content
from email_exporter import EmailExporter
from config import SEARCH_KEYWORDS, FIELDS_TO_EXTRACT

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class StudyManager:
    def __init__(self, config):
        self.config = config
        self.email_exporter = EmailExporter()

    def fetch_and_store_data(self):
        try:
            for keyword in SEARCH_KEYWORDS:
                logging.info(f"Fetching studies for keyword: {keyword}")
                
                # Fetch and extract
                studies = fetch_all_studies(FIELDS_TO_EXTRACT)
                extracted_data = extract_fields({
                    'StudyFieldsResponse': {'StudyFields': studies}
                })
                
                # Generate emails
                emails = {"sponsors": [], "investigators": []}
                for study in extracted_data:
                    sponsor_email = generate_email_content(study, "sponsor")
                    investigator_email = generate_email_content(study, "investigator")
                    
                    if sponsor_email:
                        emails["sponsors"].append({
                            "email": study.get('LeadSponsorEmail', 'sponsor@example.com'),
                            "content": sponsor_email
                        })
                    
                    if investigator_email:
                        emails["investigators"].append({
                            "email": study.get('OverallOfficialEmail', 'investigator@example.com'),
                            "content": investigator_email
                        })
                
                # Export emails to a JSON file
                filename = f"{keyword.replace(' ', '_')}_emails.json"
                self.email_exporter.save_emails(emails, filename)
                
                logging.info(f"Emails generated and saved for keyword: {keyword}")
                
        except Exception as e:
            logging.error(f"An error occurred: {str(e)}", exc_info=True)