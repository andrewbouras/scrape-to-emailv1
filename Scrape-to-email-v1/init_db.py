from models import db_manager
import logging

logging.basicConfig(level=logging.INFO)

def init_database():
    try:
        logging.info("Starting database verification...")
        
        # Verify prompts
        prompts = list(db_manager.db.scrapervl.find({"type": "prompt"}))
        logging.info(f"Total prompts found: {len(prompts)}")
        for prompt in prompts:
            logging.info(f"- {prompt['name']}")
            
        # Verify rubrics
        rubrics = list(db_manager.db.scrapervl.find({"type": "rubric"}))
        logging.info(f"Total rubrics found: {len(rubrics)}")
        for rubric in rubrics:
            logging.info(f"- {rubric['name']}")
            
        logging.info("Database verification completed successfully!")
        
    except Exception as e:
        logging.error(f"Error verifying database: {str(e)}")
        raise

if __name__ == "__main__":
    init_database()