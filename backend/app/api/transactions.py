"""
api/transactions.py — Transaction CRUD endpoints for the dashboard.

GET    /api/transactions            — List transactions (paginated, filtered)
GET    /api/transactions/<id>       — Get a single transaction
POST   /api/transactions            — Create a transaction (dashboard source)
PATCH  /api/transactions/<id>       — Update a transaction
DELETE /api/transactions/<id>       — Soft-delete a transaction

Notes:
  - Primary creation path is WhatsApp (Sprint 3)
  - Dashboard can also create/edit transactions (Sprint 5)
  - All endpoints require authentication (Sprint 6)

TODO: Implement in Sprint 5.
"""
import logging

from flask import Blueprint, jsonify

logger = logging.getLogger(__name__)

transactions_bp = Blueprint('transactions', __name__)


@transactions_bp.route('/transactions', methods=['GET'])
def list_transactions():
    """List transactions with pagination and optional filters."""
    # TODO: Sprint 5
    return jsonify({'error': 'Not implemented yet — Sprint 5'}), 501


@transactions_bp.route('/transactions/<uuid:transaction_id>', methods=['GET'])
def get_transaction(transaction_id):
    """Get a single transaction by ID."""
    # TODO: Sprint 5
    return jsonify({'error': 'Not implemented yet — Sprint 5'}), 501


@transactions_bp.route('/transactions', methods=['POST'])
def create_transaction():
    """Create a transaction from the dashboard (source: dashboard)."""
    # TODO: Sprint 5
    return jsonify({'error': 'Not implemented yet — Sprint 5'}), 501


@transactions_bp.route('/transactions/<uuid:transaction_id>', methods=['PATCH'])
def update_transaction(transaction_id):
    """Update a transaction's fields."""
    # TODO: Sprint 5
    return jsonify({'error': 'Not implemented yet — Sprint 5'}), 501


@transactions_bp.route('/transactions/<uuid:transaction_id>', methods=['DELETE'])
def delete_transaction(transaction_id):
    """Soft-delete a transaction."""
    # TODO: Sprint 5
    return jsonify({'error': 'Not implemented yet — Sprint 5'}), 501
