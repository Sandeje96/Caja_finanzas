"""
services/ai_service.py — All OpenAI interactions live here.

CRITICAL: Never call OpenAI from endpoints or other services directly.
          Always go through this service.

Responsible for:
- Intent classification (what does the user want to do?)
- Entity extraction (amount, category, date, description)
- Natural language response generation for financial queries
- Token usage logging for cost control

Intent constants:
  REGISTER_EXPENSE, REGISTER_INCOME, ATTACH_RECEIPT,
  QUERY, UPDATE_TRANSACTION, HELP, UNKNOWN

AI strategy (per PROJECT_CONTEXT.md):
  - USE AI for: classify intent, extract entities, format query responses
  - DON'T USE AI for: sums, CRUD, SQL queries, known data reconstruction

Model: gpt-4o-mini for ALL MVP calls (optimize cost).

TODO: Implement in Sprint 3.
"""
import logging
import os

logger = logging.getLogger(__name__)

# ─── Intent constants ─────────────────────────────────────────────────────────
INTENT_REGISTER_EXPENSE = 'REGISTER_EXPENSE'
INTENT_REGISTER_INCOME  = 'REGISTER_INCOME'
INTENT_ATTACH_RECEIPT   = 'ATTACH_RECEIPT'
INTENT_QUERY            = 'QUERY'
INTENT_UPDATE           = 'UPDATE_TRANSACTION'
INTENT_HELP             = 'HELP'
INTENT_UNKNOWN          = 'UNKNOWN'

VALID_INTENTS: set[str] = {
    INTENT_REGISTER_EXPENSE,
    INTENT_REGISTER_INCOME,
    INTENT_ATTACH_RECEIPT,
    INTENT_QUERY,
    INTENT_UPDATE,
    INTENT_HELP,
    INTENT_UNKNOWN,
}


class AIService:
    """Single entry point for all OpenAI API calls."""

    def classify_intent(
        self,
        message: str,
        context: list[dict],
    ) -> dict:
        """
        Classify the user's intent and extract entities in one call.

        Args:
            message: The user's latest message text
            context: Previous messages [{'role': 'user'|'assistant', 'content': '...'}]

        Returns:
            {
                'intent': 'REGISTER_EXPENSE',   # One of VALID_INTENTS
                'confidence': 0.97,              # 0.0 to 1.0
                'entities': {
                    'amount': 18000,
                    'category': 'Supermercado',
                    'description': 'supermercado',
                    'date': '2026-06-24',        # ISO format or None
                }
            }

        TODO: Implement in Sprint 3.
        """
        raise NotImplementedError("Sprint 3 — OpenAI integration")

    def generate_query_response(
        self,
        question: str,
        financial_data: dict,
        context: list[dict],
    ) -> str:
        """
        Generate a natural language response to a financial query.

        IMPORTANT: financial_data comes from FinancialSummaryService (real DB data).
        The AI only formats the answer — it never invents numbers.

        Args:
            question: The user's natural language question
            financial_data: Pre-computed data dict from FinancialSummaryService
            context: Conversation context for continuity

        Returns:
            str: Natural language response in Spanish (concise, action-oriented)

        TODO: Implement in Sprint 5.
        """
        raise NotImplementedError("Sprint 5 — query response generation")

    def _load_prompt(self, prompt_name: str) -> str:
        """Load a prompt template from the prompts/ directory."""
        prompts_dir = os.path.join(
            os.path.dirname(__file__), '..', 'prompts'
        )
        path = os.path.join(prompts_dir, f'{prompt_name}.txt')
        with open(path, 'r', encoding='utf-8') as f:
            return f.read().strip()

    def _log_ai_call(
        self,
        user_id: str,
        message_id: str,
        intent: str,
        prompt_tokens: int,
        completion_tokens: int,
        model: str,
        latency_ms: int,
        success: bool = True,
        error: str = None,
    ) -> None:
        """
        Record an AI call in ai_logs table.
        Estimates cost based on gpt-4o-mini pricing.

        TODO: Implement in Sprint 3.
        """
        # gpt-4o-mini pricing (as of 2025): $0.15/1M input, $0.60/1M output tokens
        INPUT_COST_PER_TOKEN  = 0.15  / 1_000_000
        OUTPUT_COST_PER_TOKEN = 0.60  / 1_000_000
        cost_usd = (
            (prompt_tokens     or 0) * INPUT_COST_PER_TOKEN +
            (completion_tokens or 0) * OUTPUT_COST_PER_TOKEN
        )
        # TODO: persist AILog record
        logger.debug(
            f"[AIService] intent={intent} tokens={prompt_tokens}+{completion_tokens} "
            f"cost=${cost_usd:.6f} latency={latency_ms}ms ok={success}"
        )
