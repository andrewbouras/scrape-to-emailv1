import requests
import time
import logging
from config import SEARCH_EXPRESSION

class RateLimiter:
    def __init__(self, calls_per_second=3):
        self.calls_per_second = calls_per_second
        self.last_call = 0

    def wait(self):
        now = time.time()
        time_passed = now - self.last_call
        if time_passed < (1.0 / self.calls_per_second):
            time.sleep((1.0 / self.calls_per_second) - time_passed)
        self.last_call = time.time()

rate_limiter = RateLimiter()

def fetch_studies(expr, fields, pageToken=None):
    rate_limiter.wait()
    
    base_url = "https://clinicaltrials.gov/api/v2/studies"
    params = {
        'query.cond': expr,  # Changed from 'query' to 'query.cond'
        'fields': ','.join(fields),
        'pageSize': 50,  # Increased from 1 to 50
        'format': 'json'
    }
    
    if pageToken:
        params['pageToken'] = pageToken
    
    try:
        logging.debug(f"Requesting URL: {base_url} with params: {params}")
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        logging.error(f"API Error: {str(e)}\nResponse content: {response.text}")
        raise
    except KeyboardInterrupt:
        logging.info("\nFetch interrupted by user")
        return {'studies': [], 'totalCount': 0}

def fetch_all_studies(fields, limit=None):
    """Fetch studies with an optional limit on total number of studies to retrieve."""
    all_studies = []
    next_page_token = None
    first_response = True

    try:
        while True:
            response = fetch_studies(SEARCH_EXPRESSION, fields, next_page_token)
            studies = response.get('studies', [])
            
            if not studies:
                if first_response:
                    logging.warning("No studies found in initial response")
                break
                
            all_studies.extend(studies)
            
            # Only log total on first successful response
            if first_response:
                first_response = False
                logging.info(f"Found {len(studies)} studies in first page")
            
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
            
            logging.debug(f"Retrieved {len(all_studies)} studies so far...")

            if limit and len(all_studies) >= limit:
                logging.info(f"Reached specified limit of {limit} studies")
                all_studies = all_studies[:limit]
                break
            
    except KeyboardInterrupt:
        logging.info("\nFetch interrupted by user - returning partial results")
    
    logging.info(f"Total studies retrieved: {len(all_studies)}")
    return all_studies

# Remove the example usage line that was causing the error