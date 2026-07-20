"""JSON response cleaning utilities."""

import re
import json


def clean_json_response(text: str) -> str:
    """LLM応答からJSON抽出"""
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*$', '', text)
    text = re.sub(r'^```\s*', '', text)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return match.group(0)
    return text


def safe_json_loads(text: str) -> dict:
    """Safely parse JSON with cleaning"""
    cleaned = clean_json_response(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        # Try to fix common issues
        cleaned = re.sub(r'(?<!\\)\n', '\\n', cleaned)
        cleaned = re.sub(r'(?<!\\)\r', '\\r', cleaned)
        cleaned = re.sub(r'(?<!\\)\t', '\\t', cleaned)
        cleaned = re.sub(r',\s*}', '}', cleaned)
        cleaned = re.sub(r',\s*]', ']', cleaned)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            raise