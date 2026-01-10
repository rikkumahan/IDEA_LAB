class StubLLMClient:
    def explain(self, context: dict) -> str:
        return (
            "LLM explanation unavailable.\n\n"
            "This output is based on deterministic analysis only.\n"
            "Leverage flags and market signals are factual."
        )
    
    def reword_question(self, system_prompt: str, user_prompt: str) -> str:
        """
        Stub implementation for question rewording.
        Returns None to trigger fallback to canonical wording.
        """
        return None
