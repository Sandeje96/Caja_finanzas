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
"""
import json
import logging
import os
import time
from datetime import date
from openai import OpenAI
from flask import current_app

from app.extensions import db
from app.models.ai_log import AILog

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
        user_id: str = None,
        message_id: str = None,
    ) -> dict:
        """
        Classify the user's intent and extract entities in one call.
        """
        start_time = time.time()
        
        api_key = current_app.config.get('OPENAI_API_KEY')
        if not api_key:
            logger.error("[AIService] OPENAI_API_KEY no está configurado.")
            return {'intent': INTENT_UNKNOWN, 'confidence': 0.0, 'entities': {}}
            
        client = OpenAI(api_key=api_key)
        model = current_app.config.get('OPENAI_MODEL_FAST', 'gpt-4o-mini')

        prompt_text = self._load_prompt('intent_classifier')
        prompt_text = prompt_text.replace('{today}', str(date.today()))

        messages = [{"role": "system", "content": prompt_text}]
        for ctx_msg in context:
            messages.append({"role": ctx_msg['role'], "content": ctx_msg['content']})
            
        messages.append({"role": "user", "content": message})

        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.0,
                response_format={ "type": "json_object" }
            )
            
            raw_content = response.choices[0].message.content
            parsed = json.loads(raw_content)
            
            usage = response.usage
            latency = int((time.time() - start_time) * 1000)
            self._log_ai_call(
                user_id=user_id,
                message_id=message_id,
                intent=parsed.get('intent', INTENT_UNKNOWN),
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                model=model,
                latency_ms=latency,
                success=True
            )
            
            return parsed
            
        except Exception as e:
            latency = int((time.time() - start_time) * 1000)
            logger.error(f"[AIService] OpenAI error: {e}")
            self._log_ai_call(
                user_id=user_id,
                message_id=message_id,
                intent=INTENT_UNKNOWN,
                prompt_tokens=0,
                completion_tokens=0,
                model=model,
                latency_ms=latency,
                success=False,
                error=str(e)
            )
            return {'intent': INTENT_UNKNOWN, 'confidence': 0.0, 'entities': {}}

    def generate_query_response(
        self,
        question: str,
        financial_data: dict,
        context: list[dict],
    ) -> str:
        """
        Generate a natural language response to a financial query.
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
        """
        # gpt-4o-mini pricing: $0.15/1M input, $0.60/1M output tokens
        INPUT_COST_PER_TOKEN  = 0.15  / 1_000_000
        OUTPUT_COST_PER_TOKEN = 0.60  / 1_000_000
        cost_usd = (
            (prompt_tokens     or 0) * INPUT_COST_PER_TOKEN +
            (completion_tokens or 0) * OUTPUT_COST_PER_TOKEN
        )
        
        try:
            log_entry = AILog(
                user_id=user_id,
                message_id=message_id,
                intent=intent,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=(prompt_tokens or 0) + (completion_tokens or 0),
                model=model,
                cost_usd=cost_usd,
                latency_ms=latency_ms,
                success=success,
                error_message=error
            )
            db.session.add(log_entry)
            db.session.commit()
            
            logger.debug(
                f"[AIService] intent={intent} tokens={prompt_tokens}+{completion_tokens} "
                f"cost=${cost_usd:.6f} latency={latency_ms}ms ok={success}"
            )
        except Exception as e:
            db.session.rollback()
            logger.error(f"[AIService] Failed to log AI call: {e}")
