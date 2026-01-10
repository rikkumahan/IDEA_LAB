import os
from openai import AzureOpenAI

class AzureLLMClient:
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        )
        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")

    def explain(self, context: dict) -> str:
        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an explanation layer.\n"
                        "Do NOT add advice.\n"
                        "Do NOT add new facts.\n"
                        "Explain only what is explicitly provided."
                    )
                },
                {
                    "role": "user",
                    "content": self._format_context(context)
                }
            ],
            temperature=0.2,
            max_tokens=400,
        )
        return response.choices[0].message.content.strip()

    def _format_context(self, context: dict) -> str:
        return (
            "Explain the following deterministic analysis:\n\n"
            f"{context}"
        )
