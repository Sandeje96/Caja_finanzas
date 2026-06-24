"""
services/webhook_processor.py — Main orchestrator for WhatsApp webhook events.

This service is the brain of the application. It coordinates all other services
to process an incoming WhatsApp message end-to-end.

Processing pipeline (Sprint 2+):
  1. Extract message data from WhatsApp payload
  2. Deduplicate by whatsapp_message_id
  3. Find or create user by phone number
  4. Get or create active conversation
  5. Persist incoming message
  6. Build AI context window (last N messages)
  7. Detect intent + extract entities via AIService
  8. Execute business logic based on intent
  9. Persist assistant response message
  10. Send reply via WhatsAppService

Async strategy (MVP):
  The webhook endpoint calls process_async(), which launches a daemon thread.
  This returns HTTP 200 immediately, satisfying WhatsApp's <5s requirement.
  For scaling beyond MVP, replace threading with Celery + Redis.
"""
import logging
import threading

logger = logging.getLogger(__name__)


class WebhookProcessor:
    """
    Orchestrates the complete WhatsApp message processing pipeline.
    Instantiated once per request in the webhook endpoint.
    """

    def process_async(self, payload: dict) -> None:
        """
        Launch message processing in a background daemon thread.
        Returns immediately — caller (webhook endpoint) can respond 200 at once.
        """
        thread = threading.Thread(
            target=self._process_with_context,
            args=(payload,),
            daemon=True,
            name=f"webhook-{id(payload)}",
        )
        thread.start()
        logger.debug(f"[WebhookProcessor] Launched background thread {thread.name}")

    def _process_with_context(self, payload: dict) -> None:
        """Wraps _process inside a Flask app context for DB access in threads."""
        # Import here to avoid circular imports at module load
        from app import create_app
        import os

        env = os.environ.get('FLASK_ENV', 'development')
        app = create_app(env)
        with app.app_context():
            self._process(payload)

    def _process(self, payload: dict) -> None:
        """
        Main pipeline. Runs inside a Flask app context.

        TODO: Implement in Sprint 2.
        """
        # TODO: Sprint 2 — implement full pipeline
        logger.info(f"[WebhookProcessor] Processing payload (not yet implemented): {payload}")

    def _extract_message_data(self, payload: dict) -> dict | None:
        """
        Extract relevant fields from a WhatsApp webhook payload.

        Expected payload structure:
        {
          "object": "whatsapp_business_account",
          "entry": [{
            "changes": [{
              "value": {
                "messages": [{
                  "id": "wamid.xxx",
                  "from": "5491112345678",
                  "type": "text",
                  "text": {"body": "gasté 18000 en supermercado"}
                }]
              }
            }]
          }]
        }

        Returns dict with: phone, message_id, type, content, raw_payload
        Returns None if no processable message is found.

        TODO: Implement in Sprint 2.
        """
        raise NotImplementedError("Sprint 2")

    def _handle_text_message(
        self,
        user,
        conversation,
        message_text: str,
        message_db_id: str,
    ) -> str:
        """
        Process a plain text message through the full AI pipeline.
        Returns the response text to send back to the user.

        TODO: Implement in Sprint 3 (depends on AIService).
        """
        raise NotImplementedError("Sprint 3")

    def _handle_media_message(
        self,
        user,
        conversation,
        media_data: dict,
    ) -> str:
        """
        Process an image/document message as a receipt.
        Returns the response text to send back to the user.

        TODO: Implement in Sprint 4 (depends on AttachmentService).
        """
        raise NotImplementedError("Sprint 4")
