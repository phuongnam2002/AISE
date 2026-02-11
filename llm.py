import os
import json
import time
import re
from dotenv import load_dotenv
from .config_education import LLM_PROVIDER, LLM_MODELS

load_dotenv()

openai_client = None
if LLM_PROVIDER == "openai":
    try:
        from openai import OpenAI
        if os.getenv("OPENAI_API_KEY"):
            openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"),
            base_url="https://api.thucchien.ai")
        else:
            print("Warning: OPENAI_API_KEY not found in .env file.")
    except ImportError:
        print("OpenAI library not found. Please run 'pip install openai'")
    except Exception as e:
        print(f"Failed to initialize OpenAI client: {e}")

def _call_openai(prompt: str, is_creative: bool = False):
    """The function to call OpenAI's API."""
    if not openai_client: raise ConnectionError("OpenAI client is not initialized.")
    
    response = openai_client.chat.completions.create(
        model=LLM_MODELS["openai"],
        messages=[
            {"role": "system", "content": "Bạn là một chuyên gia giáo dục đẳng cấp hàng đầu tại Việt Nam. Bạn có thể tạo ra các kế hoạch học tập, giải thích khái niệm, và các bài tập, các câu trả lời, các lời khuyên phù hợp với cấp học của học sinh, yêu cầu của học sinh và giáo viên. Tất cả output bạn trả về phải tuyệt đối tuân thủ theo yêu cầu người dùng. Nếu người dùng yêu cầu trả về dạng JSON, bạn phải trả về dạng JSON chuẩn xác và chắc chắn load được bằng json.loads()."},
            {"role": "user", "content": prompt}
        ],
        temperature=1 if is_creative else 0.01,
        response_format={"type": "json_object"}
    )
    text = response.choices[0].message.content.strip()
    num_output_tokens = response.usage.completion_tokens
    
    return text, num_output_tokens


def _call_openai_with_messages(messages: list, is_creative: bool = False, use_json_format: bool = True):
    """Call OpenAI's API with custom messages array for multi-turn conversations."""
    if not openai_client: 
        raise ConnectionError("OpenAI client is not initialized.")
    
    params = {
        "model": LLM_MODELS["openai"],
        "messages": messages,
        "temperature": 1 if is_creative else 0.01,
        "max_tokens": 8192,
    }
    
    if use_json_format:
        params["response_format"] = {"type": "json_object"}
    
    response = openai_client.chat.completions.create(**params)
    text = response.choices[0].message.content.strip()
    num_output_tokens = response.usage.completion_tokens
    
    return text, num_output_tokens


def call_llm(prompt: str, is_creative: bool = False):
    """
    Call LLM API by configuration.
    """
    max_retries = 10
    retry_delay = 10
    
    error_log_dir = "json_errors"
    os.makedirs(error_log_dir, exist_ok=True)

    for attempt in range(max_retries):
        try:
            raw_response = ""
            if LLM_PROVIDER == "openai":
                raw_response = _call_openai(prompt, is_creative)
            else:
                raise ValueError(f"Unknown LLM provider specified in config: {LLM_PROVIDER}")
            
            return raw_response

        except Exception as e:
            print(f"\nAn error occurred on LLM call attempt {attempt + 1}: {e}")

        if attempt < max_retries - 1:
            print(f"Retrying API call in {retry_delay} seconds...")
            time.sleep(retry_delay)

    print("\nLLM call failed after all retries.")
    return None


def call_llm_with_messages(messages: list, is_creative: bool = False, use_json_format: bool = False):
    """
    Call LLM API with custom messages array (for multi-turn conversations).
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        is_creative: Whether to use creative temperature
        use_json_format: Whether to enforce JSON output format
    """
    max_retries = 10
    retry_delay = 10
    
    error_log_dir = "json_errors"
    os.makedirs(error_log_dir, exist_ok=True)

    for attempt in range(max_retries):
        try:
            raw_response = ""
            if LLM_PROVIDER == "openai":
                raw_response = _call_openai_with_messages(messages, is_creative, use_json_format)
            else:
                raise ValueError(f"Unknown LLM provider specified in config: {LLM_PROVIDER}")
            
            return raw_response

        except Exception as e:
            print(f"\nAn error occurred on LLM call attempt {attempt + 1}: {e}")

        if attempt < max_retries - 1:
            print(f"Retrying API call in {retry_delay} seconds...")
            time.sleep(retry_delay)

    print("\nLLM call failed after all retries.")
    return None
