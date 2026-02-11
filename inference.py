import logging
import os
import random
from typing import Any, AsyncIterable
import httpx
from dotenv import load_dotenv
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from tenacity import (
    Retrying,
    before_sleep_log,
    stop_after_attempt,
    wait_random_exponential,
)


load_dotenv()


logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


async def async_inference(  # type: ignore
    messages: list[dict[str, str]],
    model_configuration: dict[str, Any],
) -> AsyncIterable[ChatCompletionChunk] | ChatCompletion:
    """
    Performs asynchronous inference by sending messages to multiple clients with retry logic.
    Args:
        messages (list[dict[str, str]]): The input messages to be sent for inference.
            Each message should be a dict with "role" and "content" keys.
        model_configuration (dict[str, Any]): Configuration parameters for the model.
    Returns:
        response: The response from the first successful client.
    Raises:
        AllClientsFailedError: If all clients fail to respond after retries.
        Exception: If the inference call fails after several retries.
    """
    client_settings: list[dict[str, Any]]
    # NOTE: Add more API keys if these still encounter rate limits
    client_settings = [
        {
            "api_key": os.environ.get("OPENAI_API_KEY1", os.environ.get("OPENAI_API_KEY", "")),
            "base_url": os.environ.get("OPENAI_API_BASE_URL1", None),
        },
        {
            "api_key": os.environ.get("OPENAI_API_KEY2", ""),
            "base_url": os.environ.get("OPENAI_API_BASE_URL2", None),
        },
    ]

    # Filter out settings with empty API keys
    client_settings = [s for s in client_settings if s["api_key"]]

    # Shuffle the client settings to achieve load balancing across endpoints.
    # This is useful when multiple users run the job against the same endpoints at the same time
    # This is done only once at initialization to ensure All endpoints have an equal chance to be called
    random.shuffle(client_settings)

    try:
    # if True:
        for attempt in Retrying(
            reraise=True,
            before_sleep=before_sleep_log(logger, logging.WARNING),
            wait=wait_random_exponential(multiplier=1, min=1, max=10),
            stop=stop_after_attempt(10),
        ):
            with attempt:
                for idx, client_setting in enumerate(client_settings):
                    api_key: str = client_setting["api_key"]
                    base_url: str | None = client_setting["base_url"]
                    
                    http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0, connect=10.0),
           
        )
                    # if True:
                    try:
                        client = AsyncOpenAI(
                            api_key=api_key,
                            base_url=base_url,
                            http_client=http_client,
                        )
                        response = await client.chat.completions.create(
                            messages=messages, **model_configuration,
                            response_format={"type": "json_object"}
                            
                        )
                        logger.debug(f"succeeded with API endpoint {idx}")
                        print(response)
                        return response
                    except Exception as e:
                        error_type = type(e).__name__
                        error_message = str(e)
                        logger.warning(
                            f"Inference call failed on API endpoint {idx} with error type {error_type}"
                            f" and message: {error_message}."
                        )
                        logger.debug(
                            f"Failed response from API endpoint {idx}. whole messages: {messages}"
                        )
                else:
                    raise Exception(
                        f"All {len(client_settings)} clients failed to respond in this attempt"
                    )
    except Exception as e:
        print("ERROR: ", e)
        logger.exception(
            f"Inference call failed after several retries\nInput messages were: {messages}"
        )
        raise
