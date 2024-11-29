from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    # Azure OpenAI Configuration
    AZURE_OPENAI_KEY = os.getenv('AZURE_OPENAI_KEY')
    AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
    AZURE_OPENAI_VERSION = os.getenv('AZURE_OPENAI_VERSION')
    AZURE_OPENAI_DEPLOYMENT = os.getenv('AZURE_OPENAI_DEPLOYMENT')
    
    # Application Settings
    SECRET_KEY = os.getenv('SECRET_KEY')
    TOTAL_TOKENS_PER_MINUTE = int(os.getenv('TOTAL_TOKENS_PER_MINUTE', 2000000))
    TOKEN_ENCODING = os.getenv('TOKEN_ENCODING', 'cl100k_base')
    
    # Email Configuration
    EMAIL_SENDER = os.getenv('EMAIL_SENDER')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
    SMTP_SERVER = os.getenv('SMTP_SERVER')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))

# Calculate date three months AGO (not ahead)
three_months_ago = (datetime.now() - timedelta(days=90)).strftime('%Y/%m/%d')

# Update search expression to include date range and proper v2 syntax
SEARCH_EXPRESSION = "Gastrointestinal"

FIELDS_TO_EXTRACT = [
    'protocolSection.identificationModule.nctId',
    'protocolSection.identificationModule.briefTitle',
    'protocolSection.identificationModule.officialTitle',
    'protocolSection.statusModule.overallStatus',
    'protocolSection.statusModule.startDateStruct.date',
    'protocolSection.statusModule.completionDateStruct.date',
    'protocolSection.conditionsModule.conditions',
    'protocolSection.designModule.phases',
    'protocolSection.designModule.studyType',
    'protocolSection.outcomesModule.primaryOutcomes',
    'protocolSection.outcomesModule.secondaryOutcomes',
    'protocolSection.eligibilityModule.eligibilityCriteria',
    'protocolSection.contactsLocationsModule',  # Gets all contact info
    'protocolSection.sponsorCollaboratorsModule'  # Gets sponsor info
]

SEARCH_KEYWORDS = ["Gastrointestinal"]