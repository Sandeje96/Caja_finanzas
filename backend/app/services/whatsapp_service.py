"""
services/whatsapp_service.py — WhatsApp Cloud API client.

CRITICAL: Never call WhatsApp API directly from endpoints or other services.
          Always use this service.

Responsible for:
- Sending text messages (with retry + exponential backoff)
- Verifying webhook HMAC-SHA256 signatures
- Getting media download URLs
- Downloading media files

API reference: https://developers.facebook.com/docs/whatsapp/cloud-api/
"""
import hashlib
import hmac
import logging
import time

import requests
from flask import current_app

logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 2
INITIAL_BACKOFF_SECONDS = 1


class WhatsAppService:
    """HTTP client for WhatsApp Cloud API."""

    def _base_url(self) -> str:
        version  = current_app.config.get('WHATSAPP_API_VERSION', 'v18.0')
        phone_id = current_app.config.get('WHATSAPP_PHONE_NUMBER_ID', '')
        return f"https://graph.facebook.com/{version}/{phone_id}"

    def _headers(self) -> dict:
        token = current_app.config.get('WHATSAPP_TOKEN', '')
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type':  'application/json',
        }

    # ─── Send ─────────────────────────────────────────────────────────────────

    def send_text_message(self, to_phone: str, message: str) -> bool:
        """
        Send a text message to a WhatsApp number.
        Retries up to MAX_RETRIES times with exponential backoff.

        Args:
            to_phone: Recipient phone in E.164 format (e.g. +5491112345678)
            message: Plain text message body

        Returns:
            True if sent successfully, False after all retries fail.
        """
        payload = {
            'messaging_product': 'whatsapp',
            'recipient_type':    'individual',
            'to':                to_phone,
            'type':              'text',
            'text':              {'body': message},
        }

        phone_id = current_app.config.get('WHATSAPP_PHONE_NUMBER_ID', '')
        token = current_app.config.get('WHATSAPP_TOKEN', '')
        token_status = "PRESENTE" if token else "AUSENTE"
        url = f"{self._base_url()}/messages"
        
        logger.info(
            f"\nPOST URL:\n{url}\n\n"
            f"Phone Number ID:\n{phone_id}\n\n"
            f"Token:\n{token_status}\n\n"
            f"Payload:\n{payload}\n"
        )

        for attempt in range(MAX_RETRIES + 1):
            try:
                response = requests.post(
                    url,
                    json=payload,
                    headers=self._headers(),
                    timeout=10,
                )
                
                if not response.ok:
                    logger.error(
                        f"[WhatsApp] Error de Meta (Intento {attempt + 1}).\n"
                        f"Status: {response.status_code}\n"
                        f"Response: {response.text}"
                    )
                
                response.raise_for_status()
                logger.info(f"[WhatsApp] Message sent to {to_phone} (attempt {attempt + 1})")
                return True

            except requests.HTTPError as exc:
                logger.exception(f"[WhatsApp] HTTP error traceback on attempt {attempt + 1}")
            except requests.RequestException as exc:
                logger.exception(f"[WhatsApp] Network error traceback on attempt {attempt + 1}")

            if attempt < MAX_RETRIES:
                backoff = INITIAL_BACKOFF_SECONDS * (2 ** attempt)
                logger.debug(f"[WhatsApp] Retrying in {backoff}s...")
                time.sleep(backoff)

        logger.error(f"[WhatsApp] Failed to send message to {to_phone} after {MAX_RETRIES + 1} attempts")
        return False

    # ─── Webhook verification ─────────────────────────────────────────────────

    def verify_webhook_signature(self, payload_bytes: bytes, signature_header: str) -> bool:
        """
        Verify the HMAC-SHA256 signature of an incoming webhook.

        Meta sends the signature as 'X-Hub-Signature-256: sha256=<hex>'.
        We compute our own HMAC using the app secret and compare.

        Args:
            payload_bytes: Raw request body (bytes)
            signature_header: Value of X-Hub-Signature-256 header

        Returns:
            True if signature is valid.
        """
        app_secret = current_app.config.get('WHATSAPP_TOKEN', '')
        if not app_secret:
            logger.warning("[WhatsApp] WHATSAPP_TOKEN not set — skipping signature verification")
            return True  # Allow in dev when token isn't configured

        expected = hmac.new(
            app_secret.encode('utf-8'),
            payload_bytes,
            hashlib.sha256,
        ).hexdigest()

        received = signature_header.replace('sha256=', '') if signature_header else ''
        return hmac.compare_digest(expected, received)

    # ─── Media ────────────────────────────────────────────────────────────────

    def get_media_download_url(self, media_id: str) -> str | None:
        """
        Get the temporary download URL for a WhatsApp media object.
        The URL expires in ~5 minutes.

        TODO: Used in Sprint 4 (AttachmentService).
        """
        version = current_app.config.get('WHATSAPP_API_VERSION', 'v18.0')
        try:
            response = requests.get(
                f"https://graph.facebook.com/{version}/{media_id}",
                headers=self._headers(),
                timeout=10,
            )
            response.raise_for_status()
            return response.json().get('url')
        except requests.RequestException as exc:
            logger.error(f"[WhatsApp] Failed to get media URL for {media_id}: {exc}")
            return None

    def download_media(self, media_url: str) -> bytes | None:
        """
        Download a media file from a WhatsApp media URL.
        The URL must be fetched via get_media_download_url() first.

        TODO: Used in Sprint 4 (AttachmentService).
        """
        try:
            response = requests.get(
                media_url,
                headers=self._headers(),
                timeout=30,
            )
            response.raise_for_status()
            return response.content
        except requests.RequestException as exc:
            logger.error(f"[WhatsApp] Failed to download media: {exc}")
            return None
