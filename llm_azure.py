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
        """
        Generate human-readable explanation of deterministic outputs.
        
        CONSTRAINTS:
        - Explain only what is given
        - Do NOT add advice
        - Do NOT add new facts
        - Do NOT judge the startup
        - Do NOT suggest what to build
        """
        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an explanation layer, not a decision-maker.\n\n"
                        "STRICT RULES:\n"
                        "1. Explain ONLY what is explicitly provided in the analysis\n"
                        "2. Do NOT add advice or recommendations\n"
                        "3. Do NOT add new facts or assumptions\n"
                        "4. Do NOT judge the startup idea\n"
                        "5. Do NOT suggest what to build or how to pivot\n"
                        "6. Use clear, professional language\n"
                        "7. Explain problem reality, market context, leverage, and validation class\n\n"
                        "Your role is to narrate the deterministic analysis results, not to reason."
                    )
                },
                {
                    "role": "user",
                    "content": self._format_context(context)
                }
            ],
            temperature=0.2,
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()
    
    def adapt_question_wording(
        self,
        default_wording: str,
        semantic_meaning: str,
        answer_type: str,
        context: str = None
    ) -> str:
        """
        Adapt question wording for clarity and domain relevance.
        
        CONSTRAINTS:
        - Rewrite wording only
        - Do not change meaning
        - Do not suggest answers
        - Do not add bias
        """
        context_str = f"\nUser's domain/industry: {context}" if context else ""
        
        prompt = f"""You are a question wording assistant. Your ONLY job is to rewrite questions for clarity.

STRICT RULES:
1. Rewrite the question wording ONLY for clarity and domain relevance
2. Do NOT change the semantic meaning of the question
3. Do NOT suggest answers or provide examples
4. Do NOT add bias toward any response
5. Do NOT mention: leverage, advantage, competition, strategy
6. Keep the question neutral and factual
7. The answer type is {answer_type} - do not change this

ORIGINAL QUESTION:
{default_wording}

SEMANTIC MEANING (MUST PRESERVE):
{semantic_meaning}

ANSWER TYPE: {answer_type}
{context_str}

Provide ONLY the reworded question text. No explanation, no preamble, no suggestions."""
        
        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {
                    "role": "system",
                    "content": "You rewrite questions for clarity while preserving exact meaning."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=100,
        )
        return response.choices[0].message.content.strip()

    def _format_context(self, context: dict) -> str:
        return (
            "Explain the following deterministic analysis:\n\n"
            f"{context}"
        )
