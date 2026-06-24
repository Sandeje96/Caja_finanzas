"""
api/categories.py — Category endpoints.

GET  /api/categories       — List all categories (global + user-specific)
POST /api/categories       — Create a custom user category
"""
import logging

from flask import Blueprint, jsonify

logger = logging.getLogger(__name__)

categories_bp = Blueprint('categories', __name__)


@categories_bp.route('/categories', methods=['GET'])
def list_categories():
    """List all categories available to the current user."""
    # TODO: Sprint 5
    return jsonify({'error': 'Not implemented yet — Sprint 5'}), 501


@categories_bp.route('/categories', methods=['POST'])
def create_category():
    """Create a custom user-specific category."""
    # TODO: Sprint 5
    return jsonify({'error': 'Not implemented yet — Sprint 5'}), 501
