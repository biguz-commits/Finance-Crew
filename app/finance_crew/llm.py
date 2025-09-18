import os
from dotenv import load_dotenv

from crewai import LLM

load_dotenv()

def get_llm() -> LLM:
    llm = LLM(
        model="mistralai/mistral-7b-instruct",
        api_key=os.getenv("MISTRALAI_API_KEY"),
        base_url="https://openrouter.ai/api/v1"
    )

    return llm