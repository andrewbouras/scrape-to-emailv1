from utils.azure_config import call_azure_api
import logging
import json
from models import get_prompt
from datetime import datetime

class StudyProcessor:
    def __init__(self, config):
        self.config = config
        self.processing_stats = {
            'total': 0,
            'successful': 0,
            'failed': 0,
            'processing_log': []
        }

    def validate_email_content(self, emails, study):
        """Validate email content meets requirements"""
        required_fields = ['subject', 'body', 'targeting_notes']
        
        for email_type in ['sponsor_email', 'investigator_email']:
            if not all(field in emails[email_type] for field in required_fields):
                return False
            
            # Validate minimum content requirements
            if len(emails[email_type]['body']) < 100:  # Arbitrary minimum length
                return False
                
            # Verify critical study info is included
            critical_fields = ['NCTId', 'BriefTitle', 'Phase']
            for field in critical_fields:
                if field in study and study[field] not in emails[email_type]['body']:
                    return False
                    
        return True

    def process_study(self, study):
        """Process single study with validation and logging"""
        self.processing_stats['total'] += 1
        study_id = study.get('protocolSection', {}).get('identificationModule', {}).get('nctId', 'unknown')
        
        try:
            prompt_data = get_prompt("generate_emails")
            if not prompt_data:
                raise ValueError("Email generation prompt not found")

            study_data = {
                'nctId': study.get('protocolSection', {}).get('identificationModule', {}).get('nctId'),
                'briefTitle': study.get('protocolSection', {}).get('identificationModule', {}).get('briefTitle'),
                'phase': study.get('protocolSection', {}).get('designModule', {}).get('phases', []),
                'condition': study.get('protocolSection', {}).get('conditionsModule', {}).get('conditions', []),
                'status': study.get('protocolSection', {}).get('statusModule', {}).get('overallStatus')
            }

            prompt_text = prompt_data["prompt_text"].format(
                study_data=json.dumps(study_data, indent=2)
            )
            
            response = call_azure_api(prompt_text, "email_generation", self.config)
            if not response or 'choices' not in response:
                raise ValueError("Invalid API response")

            emails = json.loads(response['choices'][0]['message']['content'])
            
            # Validate email content
            if not self.validate_email_content(emails, study):
                raise ValueError("Generated emails failed validation")

            # Validate email content before returning
            if not emails or not isinstance(emails, dict):
                raise ValueError("Invalid email format returned from API")

            processed_emails = {
                'sponsor_email': {
                    'to': study.get('leadSponsorEmail'),
                    'subject': emails.get('sponsor_email', {}).get('subject'),
                    'content': emails.get('sponsor_email', {}).get('body'),
                    'metadata': {
                        'processed_at': datetime.now().isoformat(),
                        'targeting_notes': emails.get('sponsor_email', {}).get('targeting_notes')
                    }
                },
                'investigator_email': {
                    'to': study.get('overallOfficialEmail'),
                    'subject': emails.get('investigator_email', {}).get('subject'),
                    'content': emails.get('investigator_email', {}).get('body'),
                    'metadata': {
                        'processed_at': datetime.now().isoformat(),
                        'targeting_notes': emails.get('investigator_email', {}).get('targeting_notes')
                    }
                }
            }

            self.processing_stats['successful'] += 1
            self.processing_stats['processing_log'].append({
                'study_id': study_id,
                'status': 'success',
                'timestamp': datetime.now().isoformat()
            })
            
            return processed_emails

        except Exception as e:
            self.processing_stats['failed'] += 1
            self.processing_stats['processing_log'].append({
                'study_id': study_id,
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            logging.error(f"Failed to process study {study_id}: {str(e)}", exc_info=True)
            return None

    def get_processing_stats(self):
        """Return processing statistics"""
        return self.processing_stats