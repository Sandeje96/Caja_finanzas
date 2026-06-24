"""
api/conversations.py — Conversation history endpoints (dashboard view).

GET /api/conversations                              — List conversations
GET /api/conversations/<id>/messages                — Get messages in a conversation
"""
import logging

from flask import Blueprint, jsonify

logger = logging.getLogger(__name__)

conversations_bp = Blueprint('conversations', __name__)


@conversations_bp.route('/conversations', methods=['GET'])
def list_conversations():
    """List conversations for the current user."""
    # TODO: Sprint 5
    return jsonify({'error': 'Not implemented yet — Sprint 5'}), 501


@conversations_bp.route('/conversations/<uuid:conversation_id>/messages', methods=['GET'])
def get_messages(conversation_id):
    """Get paginated messages for a specific conversation."""
    # TODO: Sprint 5
    return jsonify({'error': 'Not implemented yet — Sprint 5'}), 501
