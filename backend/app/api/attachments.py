"""
api/attachments.py — Receipt and document endpoints.

GET  /api/attachments              — List attachments (paginated gallery)
GET  /api/attachments/<id>/url     — Get a signed URL for dashboard preview/download
"""
import logging

from flask import Blueprint, jsonify

logger = logging.getLogger(__name__)

attachments_bp = Blueprint('attachments', __name__)


@attachments_bp.route('/attachments', methods=['GET'])
def list_attachments():
    """List attachments for the current user (gallery view)."""
    # TODO: Sprint 5
    return jsonify({'error': 'Not implemented yet — Sprint 5'}), 501


@attachments_bp.route('/attachments/<uuid:attachment_id>/url', methods=['GET'])
def get_signed_url(attachment_id):
    """
    Generate a temporary signed URL for a private attachment.
    URL expires after 1 hour.
    """
    # TODO: Sprint 5 (uses StorageService.generate_signed_url)
    return jsonify({'error': 'Not implemented yet — Sprint 5'}), 501
