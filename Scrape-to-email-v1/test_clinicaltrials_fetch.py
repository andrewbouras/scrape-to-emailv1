from flask import Blueprint, current_app, jsonify
import logging
import os
from api_client import fetch_all_studies
from data_extractor import extract_fields
import json
import openai
from pymongo import MongoClient
from datetime import datetime

test_bp = Blueprint('test', __name__)

logging.basicConfig(level=logging.INFO)

# Define the fields we want to extract
FIELDS_TO_EXTRACT = [
    "protocolSection.identificationModule",
    "protocolSection.statusModule",
    "protocolSection.conditionsModule", 
    "protocolSection.designModule",
    "protocolSection.outcomesModule",
    "protocolSection.eligibilityModule",
    "protocolSection.contactsLocationsModule",
    "protocolSection.sponsorCollaboratorsModule"
]

# Update search parameters with comprehensive GI conditions
SEARCH_QUERY = {
    "condition": (
        'CONDITION:"Inflammatory Bowel Disease" OR '
        'CONDITION:"Crohn Disease" OR '
        'CONDITION:"Ulcerative Colitis" OR '
        'CONDITION:"Microscopic Colitis" OR '
        'CONDITION:"Lymphocytic Colitis" OR '
        'CONDITION:"Collagenous Colitis" OR '
        'CONDITION:"Celiac Disease" OR '
        'CONDITION:"Irritable Bowel Syndrome" OR '
        'CONDITION:"Gastroesophageal Reflux Disease" OR '
        'CONDITION:"Barrett Esophagus" OR '
        'CONDITION:"Eosinophilic Esophagitis" OR '
        'CONDITION:"Peptic Ulcer" OR '
        'CONDITION:"Helicobacter Pylori Infection" OR '
        'CONDITION:"Gastritis" OR '
        'CONDITION:"Gastroparesis" OR '
        'CONDITION:"Small Intestinal Bacterial Overgrowth" OR '
        'CONDITION:"Diverticulitis" OR '
        'CONDITION:"Diverticular Disease" OR '
        'CONDITION:"Colorectal Cancer" OR '
        'CONDITION:"Colon Polyps" OR '
        'CONDITION:"Primary Sclerosing Cholangitis" OR '
        'CONDITION:"Primary Biliary Cholangitis" OR '
        'CONDITION:"Autoimmune Hepatitis" OR '
        'CONDITION:"Chronic Constipation" OR '
        'CONDITION:"Chronic Diarrhea" OR '
        'CONDITION:"Functional Dyspepsia" OR '
        'CONDITION:"Pancreatitis" OR '
        'CONDITION:"Gastrointestinal Bleeding" OR '
        'CONDITION:"Esophageal Motility Disorders" OR '
        'CONDITION:"Gastric Cancer" OR '
        'CONDITION:"Hepatocellular Carcinoma" OR '
        'CONDITION:"Pancreatic Cancer" OR '
        'CONDITION:"Liver Cirrhosis" OR '
        'CONDITION:"Fatty Liver Disease" OR '
        'CONDITION:"Portal Hypertension"'
    ),
    "main": (
        'AREA[OverallStatus]"NOT_YET_RECRUITING" AND '  # Changed to only NOT_YET_RECRUITING
        'AREA[StudyType]"INTERVENTIONAL" AND '
        '(AREA[Phase]"PHASE1" OR '
        'AREA[Phase]"PHASE2" OR '
        'AREA[Phase]"PHASE3" OR '
        'AREA[Phase]"PHASE4")'
    )
}

def evaluate_contact(contact, study_data):
    """Evaluate if and how we should contact this person"""
    
    # Skip organizations without a specific person
    if not isinstance(contact.get('name', ''), str) or contact.get('name', '').lower() == contact.get('organization', '').lower():
        return None
        
    # Skip contacts without email
    if contact.get('email', 'No email') == 'No email':
        return None
        
    role_importance = {
        'PRINCIPAL_INVESTIGATOR': 3,
        'STUDY_DIRECTOR': 3, 
        'STUDY_CHAIR': 3,
        'SUB_INVESTIGATOR': 2,
        'CONTACT': 1
    }

    evaluation = {
        'priority': role_importance.get(contact.get('role', ''), 1),
        'rationale': [],
        'custom_intro': None
    }

    # Add context about their role
    if contact['type'] == 'Overall Official':
        evaluation['rationale'].append(f"As the {contact.get('role', 'official')} at {contact.get('affiliation', 'your institution')}")
        evaluation['priority'] += 1

    elif contact['type'] == 'Site Contact':
        evaluation['rationale'].append(f"As the site contact at {contact.get('site', '')}")
        if contact.get('role') == 'PRINCIPAL_INVESTIGATOR':
            evaluation['priority'] += 2

    # Add study-specific context
    study_phase = study_data.get('protocolSection', {}).get('designModule', {}).get('phases', [])
    if study_phase and 'PHASE4' in study_phase:
        evaluation['priority'] += 1
        evaluation['rationale'].append("given your involvement in this Phase 4 study")

    return evaluation if evaluation['priority'] > 1 else None

def generate_outreach_email(config, study_data, contact):
    try:
        client = openai.AzureOpenAI(
            api_key=config['AZURE_OPENAI_KEY'],
            api_version=config['AZURE_OPENAI_VERSION'],
            azure_endpoint=config['AZURE_OPENAI_ENDPOINT']
        )

        # Extract condition names for more general reference
        conditions = study_data.get('protocolSection', {}).get('conditionsModule', {}).get('conditions', [])
        primary_condition = conditions[0] if conditions else "your therapeutic area"

        prompt = f"""Generate a professional outreach email following this exact structure and tone:

STUDY CONTEXT (for reference only - don't mention specific trial details):
- Focus Area: {primary_condition}
- Institution: {contact.get('affiliation', contact.get('site', ''))}

EMAIL TEMPLATE STRUCTURE:
1. First Paragraph:
   - Start with "Hello"
   - Brief introduction
   - Mention tool for streamlining patient screening
   - Focus on IC/EC matching capability
   - Emphasize time savings and reduced manual workload

2. Second Paragraph:
   - Reference success with other sites
   - Highlight benefits for large candidate pools
   - Mention reduction in screening time
   - Keep focus on practical benefits

3. Third Paragraph:
   - Offer free demo
   - Emphasize tailoring to their specific site
   - Mention workflow integration
   - Keep it simple and direct

4. Call-to-Action:
   - Brief, one-line invitation to respond
   - Low-pressure tone

5. Signature (use exactly):
   Best regards,
   Dhruv Patel
   Chief Marketing Officer
   Vexa Research
   dhruv@vexaresearch.com
   (703) 915-4673
   www.vexaresearch.com

FORMAT:
Subject: Streamline Patient Screening for {contact.get('affiliation', contact.get('site', '')).split(',')[0]}

[Follow the template structure above exactly, maintaining the same concise, direct tone]

TONE GUIDELINES:
- Professional but conversational
- Focus on practical benefits
- Avoid technical jargon
- Keep total length similar to template
- No mention of specific studies or trial IDs"""

        response = client.chat.completions.create(
            model=config['AZURE_OPENAI_DEPLOYMENT'],
            messages=[{
                "role": "system", 
                "content": "You are an AI that writes highly personalized and effective outreach emails for clinical trial recruitment software sales."
            }, {
                "role": "user",
                "content": prompt
            }],
            temperature=0.7,
            max_tokens=800
        )
        
        return response.choices[0].message.content

    except openai.APIError as e:
        logging.error(f"OpenAI API error: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"Error generating email: {str(e)}")
        raise

def get_unique_contact_key(contact):
    """Generate a unique key for a contact based on email and name"""
    return f"{contact.get('email', '').lower()}_{contact.get('name', '').lower()}"

def get_best_contact_info(contacts, contact_key):
    """Get the most complete contact info for a given contact key"""
    matching_contacts = [c for c in contacts if get_unique_contact_key(c) == contact_key]
    if not matching_contacts:
        return None
        
    # Prioritize contacts with more information
    best_contact = matching_contacts[0]
    for contact in matching_contacts[1:]:
        # Prefer contacts with site/organization info
        if contact.get('site') and not best_contact.get('site'):
            best_contact = contact
        # Prefer contacts with higher roles
        elif contact.get('role') in ['PRINCIPAL_INVESTIGATOR', 'STUDY_DIRECTOR'] and best_contact.get('role') not in ['PRINCIPAL_INVESTIGATOR', 'STUDY_DIRECTOR']:
            best_contact = contact
            
    return best_contact

# Add MongoDB connection setup
def get_mongo_client():
    """Get MongoDB client using configuration"""
    mongo_uri = current_app.config['MONGODB_URI']
    client = MongoClient(mongo_uri)
    return client

def check_study_contacted(db, study_id, email):
    """Check if we've already contacted this study/email combination"""
    collection = db.contacted_studies
    return collection.find_one({
        'study_id': study_id,
        'email': email
    }) is not None

def get_study_by_id(studies, study_id):
    """Helper function to find a study by its ID"""
    for study in studies:
        if study.get('protocolSection', {}).get('identificationModule', {}).get('nctId') == study_id:
            return study
    return None

def record_study_contact(db, study_id, email, contact_info, study_data):
    """Record that we've contacted this study"""
    collection = db.contacted_studies
    
    # Parse email content if it exists in contact_info
    email_content = generate_outreach_email(current_app.config, study_data, contact_info)
    subject_line = ""
    body_content = ""
    
    if email_content:
        # Split email content into subject and body
        content_parts = email_content.split('\n', 1)
        if len(content_parts) == 2:
            subject_line = content_parts[0].replace('Subject:', '').strip()
            body_content = content_parts[1].strip()
    
    contact_record = {
        'study_id': study_id,
        'email': email,
        'contact_info': contact_info,
        'contacted_at': datetime.utcnow(),
        'email_status': 'not sent',  # New field
        'subject_id': subject_line,  # New field
        'body_content': body_content,  # New field
    }
    collection.insert_one(contact_record)

@test_bp.route('/test_fetch', methods=['GET'])
def test_clinical_trials_fetch():
    try:
        # Create output directory if it doesn't exist
        output_dir = 'test_outputs'
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize set to track processed studies
        processed_study_ids = set()
        
        # Get configuration from Flask app
        config = {
            'AZURE_OPENAI_KEY': current_app.config['AZURE_OPENAI_KEY'],
            'AZURE_OPENAI_ENDPOINT': current_app.config['AZURE_OPENAI_ENDPOINT'],
            'AZURE_OPENAI_VERSION': current_app.config['AZURE_OPENAI_VERSION'],
            'AZURE_OPENAI_DEPLOYMENT': current_app.config['AZURE_OPENAI_DEPLOYMENT']
        }
        
        logging.info("Starting clinical trials fetch test...")
        
        # 1. Fetch raw data from ClinicalTrials.gov
        logging.info("Fetching studies from ClinicalTrials.gov...")
        raw_studies = fetch_all_studies(
            FIELDS_TO_EXTRACT, 
            search_query=SEARCH_QUERY,
            limit=30  # Changed from 1 to 30
        )
        logging.info(f"Retrieved {len(raw_studies)} studies")

        # Export full study details for debugging
        if raw_studies:
            first_study = raw_studies[0]
            with open(os.path.join(output_dir, 'study_debug.txt'), 'w') as f:
                json.dump(first_study, f, indent=2)
            print(f"\nFull details of first study exported to {output_dir}/study_debug.txt")
            
        # 2. Extract fields - Fix data structure
        extracted_data = []
        if raw_studies:
            for study in raw_studies:
                # Ensure study is in correct format
                if isinstance(study, dict) and 'protocolSection' in study:
                    extracted_data.append(study)
                else:
                    logging.warning(f"Skipping malformed study data: {study}")
        
        # 3. Process and display contact information
        print("\nContact Information from Studies:")
        print("-" * 50)
        
        contact_data = []
        
        for study in extracted_data:
            # Debug print study structure
            print(f"\nAnalyzing study structure for {study.get('protocolSection', {}).get('identificationModule', {}).get('nctId', 'N/A')}")
            
            study_info = {
                'nct_id': study.get('protocolSection', {}).get('identificationModule', {}).get('nctId', 'N/A'),
                'title': study.get('protocolSection', {}).get('identificationModule', {}).get('briefTitle', 'N/A'),
                'contacts': []
            }
            
            # Get all possible contact sources
            protocol = study.get('protocolSection', {})
            contacts_module = protocol.get('contactsLocationsModule', {})
            sponsor_module = protocol.get('sponsorCollaboratorsModule', {})
            oversight_module = protocol.get('oversightModule', {})
            
            print(f"Available modules:")
            print(f"- Contacts module found: {'contactsLocationsModule' in protocol}")
            print(f"- Sponsor module found: {'sponsorCollaboratorsModule' in protocol}")
            print(f"- Oversight module found: {'oversightModule' in protocol}")

            # Lead sponsor contacts
            if sponsor_module:
                lead_sponsor = sponsor_module.get('leadSponsor', {})
                if lead_sponsor:
                    study_info['contacts'].append({
                        'type': 'Lead Sponsor',
                        'name': lead_sponsor.get('name', 'No name'),
                        'organization': lead_sponsor.get('name'),
                        'email': lead_sponsor.get('email', 'No email'),
                        'phone': lead_sponsor.get('phone', 'No phone')
                    })
            
            # Central contacts
            for contact in contacts_module.get('centralContacts', []):
                study_info['contacts'].append({
                    'type': 'Central Contact',
                    'name': contact.get('name', 'No name'),
                    'email': contact.get('email', 'No email'),
                    'phone': contact.get('phone', 'No phone'),
                    'role': contact.get('role', 'No role')
                })
            
            # Overall officials/investigators
            for official in contacts_module.get('overallOfficials', []):
                study_info['contacts'].append({
                    'type': 'Overall Official',
                    'name': official.get('name', 'No name'),
                    'email': official.get('email', 'No email'),
                    'phone': official.get('phone', 'No phone'),
                    'role': official.get('role', 'No role'),
                    'affiliation': official.get('affiliation', 'No affiliation')
                })
                    
            # Location contacts
            for location in contacts_module.get('locations', []):
                if location.get('contacts'):
                    for contact in location.get('contacts', []):
                        study_info['contacts'].append({
                            'type': 'Site Contact',
                            'name': contact.get('name', 'No name'),
                            'email': contact.get('email', 'No email'),
                            'phone': contact.get('phone', 'No phone'),
                            'role': contact.get('role', 'No role'),
                            'site': location.get('facility', 'Unknown Site'),  # Changed this line
                            'city': location.get('city'),
                            'state': location.get('state'),
                            'country': location.get('country')
                        })

            # Print debug info about what we found
            print(f"\nFound {len(study_info['contacts'])} contacts:")
            for contact in study_info['contacts']:
                print(f"- {contact['type']}: {contact['name']}")
                if contact.get('email'): print(f"  Email: {contact['email']}")
                if contact.get('phone'): print(f"  Phone: {contact['phone']}")

            if study_info['contacts']:
                contact_data.append(study_info)

        # 4. Save contact information to file
        with open(os.path.join(output_dir, 'study_contacts.json'), 'w') as f:
            json.dump(contact_data, f, indent=2)
        print(f"\nContact information saved to {output_dir}/study_contacts.json")
        print(f"Total studies with contact information: {len(contact_data)}")
        
        # Initialize MongoDB connection
        mongo_client = get_mongo_client()
        db = mongo_client.VexaMarketing
        
        emails = []
        if raw_studies and len(contact_data) > 0:
            # Track already processed study/email combinations
            processed_contacts = set()
            
            for study in raw_studies:
                study_id = study.get('protocolSection', {}).get('identificationModule', {}).get('nctId')
                
                # Skip if we can't get a study ID
                if not study_id:
                    continue
                
                study_contacts = []
                for contact_info in contact_data:
                    if contact_info['nct_id'] == study_id:
                        for contact in contact_info['contacts']:
                            # Skip contacts without email
                            if contact.get('email', 'No email') == 'No email':
                                continue
                                
                            # Create unique contact identifier
                            contact_key = f"{study_id}_{contact['email']}"
                            
                            # Skip if we've already processed this contact
                            if contact_key in processed_contacts:
                                continue
                                
                            # Check if we've already contacted this study/email combination
                            if check_study_contacted(db, study_id, contact['email']):
                                logging.info(f"Skipping already contacted study/email: {study_id}/{contact['email']}")
                                continue
                            
                            processed_contacts.add(contact_key)
                            study_contacts.append(contact)
                
                if study_contacts:
                    # Generate emails for unique contacts
                    for contact in study_contacts:
                        email_content = generate_outreach_email(config, study, contact)
                        emails.append({
                            "contact": contact,
                            "email_content": email_content,
                            "study_id": study_id
                        })
                        
                        # Record this contact in MongoDB - now passing the full study object
                        record_study_contact(db, study_id, contact['email'], contact, study)
                    
                    processed_study_ids.add(study_id)
            
            # Save generated emails
            with open(os.path.join(output_dir, 'generated_emails.json'), 'w') as f:
                json.dump(emails, f, indent=2)
            print(f"\nGenerated {len(emails)} personalized emails using Azure OpenAI, saved to {output_dir}/generated_emails.json")

        # Close MongoDB connection
        mongo_client.close()

        # Always return a response, even if no emails were generated
        return jsonify({
            'status': 'success',
            'message': f"Successfully processed {len(raw_studies)} studies",
            'contacts_found': len(contact_data),
            'emails_generated': len(emails),
            'output_files': {
                'study_debug': f"{output_dir}/study_debug.txt",
                'study_contacts': f"{output_dir}/study_contacts.json",
                'generated_emails': f"{output_dir}/generated_emails.json" if emails else None
            }
        })

    except Exception as e:
        logging.error(f"Error processing studies: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@test_bp.route('/test_mongo', methods=['GET'])
def test_mongo_connection():
    """Test route to verify MongoDB connection and study tracking"""
    try:
        # Initialize MongoDB connection
        mongo_client = get_mongo_client()
        db = mongo_client.VexaMarketing
        
        # Get count of existing records
        existing_count = db.contacted_studies.count_documents({})
        
        # Test record
        test_record = {
            'study_id': 'TEST_NCT123',
            'email': 'test@example.com',
            'contact_info': {'name': 'Test Contact', 'role': 'TEST'},
            'contacted_at': datetime.utcnow()
        }
        
        # Insert test record
        db.contacted_studies.insert_one(test_record)
        
        # Verify the record was inserted
        new_count = db.contacted_studies.count_documents({})
        test_found = db.contacted_studies.find_one({'study_id': 'TEST_NCT123'})
        
        # Clean up test record
        db.contacted_studies.delete_one({'study_id': 'TEST_NCT123'})
        
        # Close connection
        mongo_client.close
        
        return jsonify({
            'status': 'success',
            'message': 'MongoDB connection test successful',
            'details': {
                'existing_records': existing_count,
                'after_insert': new_count,
                'test_record_found': test_found is not None
            }
        })

    except Exception as e:
        logging.error(f"MongoDB test error: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Add a simple index route
@test_bp.route('/', methods=['GET'])
def index():
    return """
    <h1>Clinical Trials Email Generator Test Interface</h1>
    <p>Available endpoints:</p>
    <ul>
        <li><a href="/test/test_fetch">Test Fetch</a> - Fetch and process clinical trials</li>
    </ul>
    """