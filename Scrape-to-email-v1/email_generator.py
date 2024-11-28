from utils.azure_config import call_azure_api

def generate_email_content(study, recipient_type="sponsor"):
    """Generate email content based on study data and recipient type"""
    
    study_data = {
        'nctId': study.get('nct_id'),
        'briefTitle': study.get('brief_title'),
        'phase': study.get('phase', []),
        'condition': study.get('conditions', []),
        'status': study.get('status')
    }
    
    prompt = {
        'sponsor': """Generate a professional email for this clinical trial sponsor:
        STUDY DATA: {study_data}
        Focus on how Vexa can help with patient recruitment.""",
        'investigator': """Generate a professional email for this clinical trial investigator:
        STUDY DATA: {study_data} 
        Focus on how Vexa can help with their recruitment efforts."""
    }
    
    return {
        'subject': f"Vexa Research - Patient Recruitment for {study_data['briefTitle']}",
        'content': prompt[recipient_type].format(study_data=study_data)
    }