class StubLLMClient:
    def explain(self, context: dict) -> str:
        return (
            "LLM explanation unavailable.\n\n"
            "This output is based on deterministic analysis only.\n"
            "Leverage flags and market signals are factual."
        )
