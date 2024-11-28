from flask import Blueprint, current_app, jsonify
import logging
import os
from api_client import fetch_all_studies
from data_extractor import extract_fields
from config import FIELDS_TO_EXTRACT
import json
import openai  # Change to just import openai

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
    "protocolSection.contactsLocationsModule",  # Add this to get contacts/locations
    "protocolSection.sponsorCollaboratorsModule"  # Add this to get sponsor info
]

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
    """Use Azure OpenAI to generate a personalized outreach email"""
    try:
        client = openai.AzureOpenAI(
            api_key=config['AZURE_OPENAI_KEY'],
            api_version=config['AZURE_OPENAI_VERSION'],
            azure_endpoint=config['AZURE_OPENAI_ENDPOINT']
        )

        prompt = f"""Generate a professional outreach email following these guidelines and data:

STUDY DATA:
- Title: {study_data.get('protocolSection', {}).get('identificationModule', {}).get('briefTitle')}
- NCT ID: {study_data.get('protocolSection', {}).get('identificationModule', {}).get('nctId')}
- Conditions: {', '.join(study_data.get('protocolSection', {}).get('conditionsModule', {}).get('conditions', []))}
- Phase: {', '.join(study_data.get('protocolSection', {}).get('designModule', {}).get('phases', []))}
- Status: {study_data.get('protocolSection', {}).get('statusModule', {}).get('overallStatus')}

CONTACT INFO:
- Name: {contact.get('name')}
- Role: {contact.get('role')}
- Type: {contact.get('type')}
- Affiliation: {contact.get('affiliation', contact.get('site', ''))}

VEXA CONTEXT:
- Company: Vexa Research - AI-powered clinical trial recruitment platform
- Core Value: Accelerating recruitment through intelligent patient matching
- Track Record: Proven success in similar therapeutic areas
- Leadership: Dhruv Gramopadhye, CEO (dhruv@vexaresearch.com)

EMAIL REQUIREMENTS:
1. Subject Line:
   - Action-oriented and specific
   - Include study focus or institution name
   - Avoid spam trigger words

2. Salutation & Tone:
   - Use professional title (Dr.) when addressing clinical professionals
   - Maintain formal yet approachable tone
   - Avoid overly casual language

3. Introduction (First Paragraph):
   - Reference specific study details (title, NCT ID)
   - Keep concise and direct
   - Show understanding of their research area

4. Body (Second Paragraph):
   - Focus on 1-2 key value propositions
   - Connect solutions to their specific challenges
   - Use clear, concrete language
   - Avoid unnecessary jargon

5. Call-to-Action (Final Paragraph):
   - Suggest specific next steps (brief call)
   - Mention tangible benefits (case studies, examples)
   - Keep it professional and low-pressure

6. Signature:
   - Full name and title
   - Company name
   - Email
   - [Phone Number]
   - [Website]

FORMAT:
Subject: [Clear, specific subject line]

[Email body following above structure]

[Professional signature block]

TONE GUIDELINES:
- Professional but not stiff
- Helpful but not pushy
- Knowledgeable but not condescending
- Brief but informative

Keep the total email length to 200-250 words maximum."""

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

@test_bp.route('/test_fetch', methods=['GET'])
def test_clinical_trials_fetch():
    try:
        # Create output directory if it doesn't exist
        output_dir = 'test_outputs'
        os.makedirs(output_dir, exist_ok=True)
        
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
        raw_studies = fetch_all_studies(FIELDS_TO_EXTRACT, limit=1)  # Changed limit to 1
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
        
        emails = []
        if raw_studies and len(contact_data) > 0:
            study_data = raw_studies[0]
            
            for study_info in contact_data:
                for contact in study_info['contacts']:
                    # Skip non-person contacts or those without email
                    if (contact.get('name', '').lower() == contact.get('organization', '').lower() or 
                        contact.get('email', 'No email') == 'No email'):
                        continue
                        
                    email_content = generate_outreach_email(config, study_data, contact)
                    emails.append({
                        "contact": contact,
                        "email_content": email_content
                    })
            
            # Save generated emails
            with open(os.path.join(output_dir, 'generated_emails.json'), 'w') as f:
                json.dump(emails, f, indent=2)
            print(f"\nGenerated {len(emails)} personalized emails using Azure OpenAI, saved to {output_dir}/generated_emails.json")
        
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