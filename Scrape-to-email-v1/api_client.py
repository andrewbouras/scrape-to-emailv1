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

def fetch_all_studies(fields_to_extract, search_query=None, limit=None):
    """
    Fetch studies from ClinicalTrials.gov API with optional search parameters
    """
    base_url = "https://clinicaltrials.gov/api/v2/studies"
    
    # Build query parameters
    params = {
        'fields': ','.join(fields_to_extract),
        'format': 'json'
    }
    
    # Add search parameters if provided
    if search_query:
        if 'condition' in search_query:
            params['query.cond'] = search_query['condition']
            
        if 'main' in search_query:
            params['query.term'] = search_query['main']
    
    # Add limit if specified
    if limit:
        params['pageSize'] = str(limit)

    try:
        logging.info(f"Requesting URL: {base_url} with params: {params}")
        response = requests.get(base_url, params=params)
        
        if response.status_code != 200:
            logging.error(f"API Response: {response.text}")
        
        response.raise_for_status()
        data = response.json()
        return data.get('studies', [])
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching studies: {str(e)}")
        raise

# Remove the example usage line that was causing the error