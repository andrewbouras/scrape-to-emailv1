from flask import Blueprint, request, jsonify, current_app
import logging
from utils.azure_config import call_azure_api
import json
from utils.rate_limiter import AdaptiveRateLimiter
from models import get_prompt

upload_bp = Blueprint('upload', __name__)

def generate_question_summary(content, config, rate_limiter):
    prompt_data = get_prompt("generate_question_summary")
    if not prompt_data:
        raise ValueError("Prompt not found")
    
    prompt_text = prompt_data["regular_prompt"]
    variables = prompt_data["variables"]

    summary_prompt = prompt_text.format(content=content)

    rate_limiter.add_request('summary', summary_prompt)
    response = call_azure_api(summary_prompt, "summary", config)
    
    if response and 'choices' in response and response['choices']:
        summary_content = response['choices'][0]['message']['content']
        return json.loads(summary_content)
    else:
        raise ValueError("Failed to generate summary")
