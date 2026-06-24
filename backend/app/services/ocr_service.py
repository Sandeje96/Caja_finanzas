"""
services/ocr_service.py — Servicio puro para procesamiento de imágenes con IA.

Responsabilidades:
- Recibir una imagen en base64.
- Llamar a OpenAI Vision (gpt-4o-mini).
- Validar y normalizar la respuesta estructurada.
- Registrar latencia y tokens en la base de datos (auditoría).
- NO modificar entidades de base de datos ni interactuar con Attachments.
"""
import json
import logging
import os
import time
from typing import Tuple

from openai import OpenAI
from flask import current_app

from app.extensions import db
from app.models.ai_log import AILog

logger = logging.getLogger(__name__)


class OCRService:
    def __init__(self):
        self._prompt_text = self._load_prompt('ocr_system_prompt')

    def analyze_receipt_from_url(
        self,
        image_url: str,
        user_id: str = None,
        message_id: str = None
    ) -> Tuple[dict, float]:
        """
        Analiza una imagen usando gpt-4o-mini Vision mediante una URL pública/firmada.
        """
        start_time = time.time()
        api_key = current_app.config.get('OPENAI_API_KEY')
        if not api_key:
            logger.error("[OCRService] OPENAI_API_KEY no está configurado.")
            return {}, 0.0

        client = OpenAI(api_key=api_key)
        model = current_app.config.get('OPENAI_MODEL_FAST', 'gpt-4o-mini')

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": self._prompt_text},
                            {"type": "image_url", "image_url": {"url": image_url}}
                        ]
                    }
                ],
                max_tokens=300,
                temperature=0.0,
            )

            raw_content = response.choices[0].message.content.strip()
            # Ocasionalmente el modelo puede ignorar el instruction y retornar bloque markdown
            if raw_content.startswith('```json'):
                raw_content = raw_content[7:]
            if raw_content.endswith('```'):
                raw_content = raw_content[:-3]
                
            parsed = json.loads(raw_content)
            confidence = float(parsed.get('confidence', 0.0))
            
            # Log usage
            usage = response.usage
            latency = int((time.time() - start_time) * 1000)
            self._log_usage(
                user_id=user_id,
                message_id=message_id,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                model=model,
                latency_ms=latency,
                success=True
            )

            return parsed, confidence

        except Exception as e:
            latency = int((time.time() - start_time) * 1000)
            logger.error(f"[OCRService] OpenAI OCR error: {e}")
            self._log_usage(
                user_id=user_id,
                message_id=message_id,
                prompt_tokens=0,
                completion_tokens=0,
                model=model,
                latency_ms=latency,
                success=False,
                error=str(e)
            )
            return {}, 0.0

    def _load_prompt(self, prompt_name: str) -> str:
        prompts_dir = os.path.join(
            os.path.dirname(__file__), '..', 'prompts'
        )
        path = os.path.join(prompts_dir, f'{prompt_name}.txt')
        with open(path, 'r', encoding='utf-8') as f:
            return f.read().strip()

    def _log_usage(self, user_id, message_id, prompt_tokens, completion_tokens, model, latency_ms, success, error=None):
        INPUT_COST_PER_TOKEN  = 0.15  / 1_000_000
        OUTPUT_COST_PER_TOKEN = 0.60  / 1_000_000
        
        # Imagenes en Vision cuestan tokens también (gpt-4o-mini es barato igual)
        cost_usd = (
            (prompt_tokens     or 0) * INPUT_COST_PER_TOKEN +
            (completion_tokens or 0) * OUTPUT_COST_PER_TOKEN
        )
        try:
            log_entry = AILog(
                user_id=user_id,
                message_id=message_id,
                intent='OCR_PROCESS',
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
            logger.debug(f"[OCRService] cost=${cost_usd:.6f} latency={latency_ms}ms ok={success}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"[OCRService] Failed to log AI call: {e}")
