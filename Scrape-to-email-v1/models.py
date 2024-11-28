import logging

class DatabaseManager:
    def __init__(self):
        self.prompts = {
            "process_study": {
                "name": "process_study",
                "prompt_text": "Analyze the following clinical trial data and extract key insights, focusing on patient eligibility, interventions, and outcomes: {study_data}",
                "description": "Processes raw clinical trial data"
            },
            "extract_statements": {
                "name": "extract_statements",
                "prompt_text": "From the following clinical trial text, extract factual statements about the study: {chunk}",
                "description": "Extracts factual statements from text chunks"
            },
            "improve_statements": {
                "name": "improve_statements",
                "prompt_text": "Review and improve the following statements according to this rubric:\n{rubric}\n\nStatements to improve:\n{statements}",
                "description": "Improves extracted statements"
            },
            "generate_question_summary": {
                "name": "generate_question_summary",
                "regular_prompt": "Generate a structured summary of the following content: {content}",
                "variables": ["content"],
                "description": "Generates summary of study questions"
            },
            "generate_emails": {
                "name": "generate_emails",
                "prompt_text": """Generate two professional emails for this clinical trial:

STUDY DATA:
{study_data}

COMPANY CONTEXT:
- Company: Vexa Research LLC
- Core Service: Patient Recruitment Automation System
- Value Proposition: Streamlined, technology-driven patient recruitment with HIPAA compliance
- Key Features: EHR integration, automated screening, secure data handling
- Contact: Andrew@VexaResearch.com, (703) 915-4673

OUTPUT FORMAT:
{
    "sponsor_email": {
        "subject": "Vexa Research - Automated Patient Recruitment for [Trial Phase] [Condition] Study",
        "body": "[Email Body]",
        "targeting_notes": "[Notes about email targeting strategy]"
    },
    "investigator_email": {
        "subject": "Vexa Research - Patient Recruitment Solution for [Study ID]",
        "body": "[Email Body]",
        "targeting_notes": "[Notes about email targeting strategy]"
    }
}

REQUIREMENTS:
1. Use study phase, condition, and NCT ID from the study data
2. Minimum 200 words per email body
3. Focus on relevant study details and recruitment capabilities
4. Maintain professional tone
5. Include contact information in signature
""",
                "description": "Generates Vexa Research-branded emails for sponsors and investigators"
            }
        }
        self.rubrics = {
            "statement_improvement_rubric": {
                "name": "statement_improvement_rubric",
                "rubric_text": "1. Ensure statements are clear and concise\n2. Remove redundant information\n3. Use consistent medical terminology\n4. Maintain factual accuracy\n5. Format in complete sentences\n6. Include relevant numerical data\n7. Preserve study-specific details\n8. Use active voice where possible",
                "description": "Rubric for improving clinical trial statements"
            }
        }
        
    def setup_database(self):
        """Initialize database with required prompts and rubrics"""
        try:
            logging.info("Setting up database...")
            # For now, just verify the in-memory data structures are initialized
            if self.prompts and self.rubrics:
                logging.info("Database setup complete - prompts and rubrics initialized")
            else:
                logging.warning("Database setup warning - some data structures may be empty")
        except Exception as e:
            logging.error(f"Database setup failed: {str(e)}")
            raise

    def get_prompt(self, name):
        return self.prompts.get(name)

    def get_rubric(self, name):
        return self.rubrics.get(name)

# Singleton instance
db_manager = DatabaseManager()
get_prompt = db_manager.get_prompt
get_rubric = db_manager.get_rubric