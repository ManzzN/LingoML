import re
import openai
import logging
from config import OPENAI_API_KEY

# Initialize once
openai.api_key = OPENAI_API_KEY


def extract_json(response: str) -> str:
    """
    Tries to strip away any ``` blocks from the response so it can be parsed as JSON.
    """
    response = response.strip()
    if response.startswith("```"):
        lines = response.splitlines()
        if len(lines) > 0 and lines[0].startswith("```"):
            lines = lines[1:]
        if len(lines) > 0 and lines[-1].startswith("```"):
            lines = lines[:-1]
        response = "\n".join(lines).strip()
    return response


def call_llm(prompt: str) -> str:
    """
    Simple wrapper to call the LLM with a single user prompt. 
    Returns the first response or an error string.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-0613",  # Or whichever model you prefer
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Error calling OpenAI: {e}")
        return "Error: Could not generate response."
