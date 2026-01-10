class StubLLMClient:
    def explain(self, context: dict) -> str:
        return (
            "LLM explanation unavailable.\n\n"
            "This output is based on deterministic analysis only.\n"
            "Leverage flags and market signals are factual."
        )
    
    def adapt_question_wording(
        self,
        default_wording: str,
        semantic_meaning: str,
        answer_type: str,
        context: str = None
    ) -> str:
        """
        Stub: Returns default wording without LLM adaptation.
        
        This allows the system to work without LLM configured.
        """
        return default_wording
