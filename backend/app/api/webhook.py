"""
api/webhook.py — WhatsApp Cloud API webhook endpoints.

GET  /api/webhook — Meta verification challenge (required before using the API)
POST /api/webhook — Incoming WhatsApp messages

Design:
  The POST handler MUST return HTTP 200 within 5 seconds.
  All heavy processing is delegated to WebhookProcessor.process_async()
  which runs in a background thread.

References:
  https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks
"""
import logging

from flask import Blueprint, current_app, jsonify, request

from app.services.webhook_processor import WebhookProcessor

logger = logging.getLogger(__name__)

webhook_bp = Blueprint('webhook', __name__)
_processor = WebhookProcessor()


@webhook_bp.route('/webhook', methods=['GET'])
def verify_webhook():
    """
    WhatsApp webhook verification handshake.

    Meta sends:
      hub.mode = 'subscribe'
      hub.verify_token = <your verify token>
      hub.challenge = <random string to echo back>

    We must respond with hub.challenge if the token matches.
    """
    mode      = request.args.get('hub.mode')
    token     = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    verify_token = current_app.config.get('WHATSAPP_VERIFY_TOKEN', '')

    logger.info(f"[Webhook] GET /webhook - request.args: {dict(request.args)}")
    logger.info(f"[Webhook] hub.mode: {mode}")
    logger.info(f"[Webhook] hub.challenge: {challenge}")
    logger.info(f"[Webhook] hub.verify_token: {token}")
    logger.info(f"[Webhook] WHATSAPP_VERIFY_TOKEN (config): {verify_token}")
    logger.info(f"[Webhook] Tokens coinciden?: {token == verify_token}")

    if mode == 'subscribe' and token == verify_token:
        logger.info("[Webhook] ✅ Verification successful")
        return challenge, 200

    logger.warning(
        f"[Webhook] ❌ Verification failed — "
        f"mode={mode}, token_match={token == verify_token}"
    )
    return jsonify({'error': 'Forbidden'}), 403


@webhook_bp.route('/webhook', methods=['POST'])
def receive_message():
    """
    Receive incoming WhatsApp webhook events.

    MUST return HTTP 200 immediately.
    Actual processing happens in a background thread via process_async().
    """
    payload = request.get_json(silent=True) or {}

    # WhatsApp only sends whatsapp_business_account events; ignore others
    if payload.get('object') != 'whatsapp_business_account':
        logger.debug("[Webhook] Ignored non-WhatsApp event")
        return jsonify({'status': 'ignored'}), 200

    # Launch background processing — never block this handler
    _processor.process_async(payload)

    # Respond immediately so WhatsApp doesn't retry
    return jsonify({'status': 'ok'}), 200
