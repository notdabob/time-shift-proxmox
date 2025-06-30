#!/usr/bin/env python3
"""
AI Provider API Key Validator

This script reads the .env file, checks for configured AI provider keys,
and tests their validity by sending a simple prompt.
"""

import os
import sys
from dotenv import load_dotenv

# --- Helper for colored output ---
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_success(message):
    print(f"{bcolors.OKGREEN}{message}{bcolors.ENDC}")

def print_error(message):
    print(f"{bcolors.FAIL}{message}{bcolors.ENDC}")

def print_warning(message):
    print(f"{bcolors.WARNING}{message}{bcolors.ENDC}")

def print_info(message):
    print(f"{bcolors.OKCYAN}{message}{bcolors.ENDC}")

def print_header(message):
    print(f"{bcolors.HEADER}{bcolors.BOLD}{message}{bcolors.ENDC}")

# --- AI Provider Test Functions ---

def test_gemini(api_key, model):
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model_instance = genai.GenerativeModel(model)
        model_instance.generate_content("hello")
        return True, "OK"
    except Exception as e:
        return False, str(e)

def test_anthropic(api_key, model):
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        client.messages.create(
            model=model,
            max_tokens=10,
            messages=[{"role": "user", "content": "hello"}]
        )
        return True, "OK"
    except Exception as e:
        return False, str(e)

def test_openai(api_key, model):
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        client.chat.completions.create(
            model=model if model else "gpt-3.5-turbo", # Default model if not set
            messages=[{"role": "user", "content": "hello"}]
        )
        return True, "OK"
    except Exception as e:
        return False, str(e)

def test_perplexity(api_key, model):
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")
        client.chat.completions.create(
            model=model if model else "llama-3-sonar-small-32k-online", # Default model
            messages=[{"role": "user", "content": "hello"}]
        )
        return True, "OK"
    except Exception as e:
        return False, str(e)

def test_groq(api_key, model):
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "hello"}],
            max_tokens=10
        )
        return True, "OK"
    except Exception as e:
        return False, str(e)

# --- Main Logic ---

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    env_path = os.path.join(project_root, '.env')

    if not os.path.exists(env_path):
        print_error(f"Error: .env file not found at {env_path}")
        sys.exit(1)

    load_dotenv(dotenv_path=env_path)

    providers = [
        {"name": "Google Gemini", "key_var": "GEMINI_API_KEY", "model_var": "GEMINI_MODEL", "test_func": test_gemini, "placeholder_prefixes": ["AIzaSy"]},
        {"name": "Anthropic Claude", "key_var": "ANTHROPIC_API_KEY", "model_var": "CLAUDE_MODEL", "test_func": test_anthropic},
        {"name": "OpenAI", "key_var": "OPENAI_API_KEY", "model_var": "OPENAI_MODEL", "test_func": test_openai},
        {"name": "Perplexity", "key_var": "PERPLEXITY_API_KEY", "model_var": "PERPLEXITY_MODEL", "test_func": test_perplexity},
        {"name": "Groq", "key_var": "GROQ_API_KEY", "model_var": "GROQ_MODEL", "test_func": test_groq},
    ]

    print_header("1. AI Provider Configuration Status")
    print("="*40)

    configured_providers = []
    for provider in providers:
        api_key = os.getenv(provider["key_var"])
        model = os.getenv(provider["model_var"])
        
        is_valid = True
        if not api_key or "your_api_key" in api_key or "your_project_id" in api_key:
            status_msg = f"[{bcolors.FAIL}✗{bcolors.ENDC}] {provider['name']:<20} - Key not set or is a placeholder."
            is_valid = False
        else:
            model_info = f" (Model: {model})" if model else " (Model: Not set)"
            status_msg = f"[{bcolors.OKGREEN}✓{bcolors.ENDC}] {provider['name']:<20} - Key configured.{model_info}"
        
        print(status_msg)
        if is_valid:
            provider['api_key'] = api_key
            provider['model'] = model
            configured_providers.append(provider)

    print("\n" + "="*40)
    print_header("\n2. Testing API Key Validity")
    print("="*40)

    if not configured_providers:
        print_warning("No valid provider configurations found to test.")
        sys.exit(0)

    try:
        import google.generativeai, anthropic, openai, groq
    except ImportError as e:
        print_error(f"Missing required Python packages. Please install them.")
        print_info(f"Hint: pip install -r requirements.txt")
        print_error(f"Details: {e}")
        sys.exit(1)

    for provider in configured_providers:
        sys.stdout.write(f"  - Testing {provider['name']:<20} ... ")
        sys.stdout.flush()

        if not provider.get('model') and provider['name'] not in ['OpenAI', 'Perplexity']:
            print_error(f"[{bcolors.FAIL}✗{bcolors.ENDC}] Error: Model not set for {provider['name']}.")
            continue

        success, message = provider["test_func"](provider["api_key"], provider["model"])

        if success:
            print_success(f"[{bcolors.OKGREEN}✓{bcolors.ENDC}] Valid")
        else:
            print_error(f"[{bcolors.FAIL}✗{bcolors.ENDC}] Error")
            print_error(f"    Details: {message}")

    print("\n" + "="*40)
    print_info("Done.")

if __name__ == "__main__":
    main()