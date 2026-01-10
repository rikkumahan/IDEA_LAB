import os
from llm_stub import StubLLMClient

def get_llm_client():
    if os.getenv("AZURE_OPENAI_API_KEY"):
        from llm_azure import AzureLLMClient
        return AzureLLMClient()
    return StubLLMClient()
