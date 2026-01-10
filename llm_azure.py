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
        Generate explanation for deterministic analysis results.
        
        CRITICAL CONSTRAINTS (enforced in prompt):
        - Explain ONLY what is given
        - Do NOT add advice
        - Do NOT add new facts
        - Do NOT judge the startup
        - Do NOT suggest actions
        - You are an explanation layer, NOT a decision-maker
        """
        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an explanation layer, NOT a decision-maker.\n\n"
                        "CRITICAL RULES:\n"
                        "- Explain ONLY what is explicitly provided in the context\n"
                        "- Do NOT add advice or recommendations\n"
                        "- Do NOT add new facts or assumptions\n"
                        "- Do NOT judge whether the startup will succeed\n"
                        "- Do NOT suggest actions or strategies\n"
                        "- Do NOT infer beyond what is stated\n\n"
                        "Your role is to narrate the deterministic results clearly, "
                        "not to reason about them or extend them."
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
    
    def reword_question(self, system_prompt: str, user_prompt: str) -> str:
        """
        Reword a question for better clarity while preserving exact meaning.
        
        This is used ONLY for question wording adaptation (UX layer).
        The LLM must NOT change the semantic meaning.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                # Low temperature (0.1) for minimal creativity and maximum consistency
                # This ensures rewording stays very close to original meaning
                # Higher values (>0.3) might introduce unintended semantic drift
                temperature=0.1,
                max_tokens=150,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            # If LLM fails, return None to trigger fallback to canonical wording
            return None

    def _format_context(self, context: dict) -> str:
        """Format context for explanation prompt."""
        parts = ["Explain the following deterministic analysis:\n"]
        
        # Format Stage 1: Problem Reality
        if "stage_1_problem" in context:
            parts.append("\n=== STAGE 1: PROBLEM REALITY ===")
            stage1 = context["stage_1_problem"]
            parts.append(f"Problem Level: {stage1.get('problem_level', 'UNKNOWN')}")
            if "signals" in stage1:
                signals = stage1["signals"]
                parts.append(f"Signals: {signals}")
        
        # Format Stage 2: Market Reality
        if "stage_2_market" in context:
            parts.append("\n=== STAGE 2: MARKET REALITY ===")
            stage2 = context["stage_2_market"]
            if "market_strength" in stage2:
                parts.append(f"Market Strength: {stage2['market_strength']}")
        
        # Format Stage 3: Leverage Reality
        if "stage_3_leverage" in context:
            parts.append("\n=== STAGE 3: LEVERAGE REALITY ===")
            stage3 = context["stage_3_leverage"]
            leverage_flags = stage3.get("leverage_flags", [])
            parts.append(f"Leverage Flags: {', '.join(leverage_flags) if leverage_flags else 'NONE'}")
            if "leverage_details" in stage3:
                parts.append(f"Details: {stage3['leverage_details']}")
        
        # Format Validation
        if "validation" in context:
            parts.append("\n=== VALIDATION STATE ===")
            validation = context["validation"]
            parts.append(f"Problem Validity: {validation.get('problem_validity', 'UNKNOWN')}")
            parts.append(f"Leverage Presence: {validation.get('leverage_presence', 'UNKNOWN')}")
            parts.append(f"Validation Class: {validation.get('validation_class', 'UNKNOWN')}")
        
        return "\n".join(parts)
