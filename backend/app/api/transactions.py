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
from flask import Blueprint, jsonify, request, g
from app.utils.decorators import jwt_required
from app.repositories.transaction_repository import TransactionRepository
from app.models.transaction import Transaction
from app.models.audit_log import AuditLog
from app.extensions import db
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

transactions_bp = Blueprint('transactions', __name__)
transaction_repo = TransactionRepository()

@transactions_bp.route('/transactions', methods=['GET'])
@jwt_required
def list_transactions():
    """List transactions with pagination and optional filters."""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))
    # In a real scenario, we'd add filters here
    
    query = Transaction.query.filter_by(user_id=g.current_user_id, deleted_at=None).order_by(Transaction.transaction_date.desc(), Transaction.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'items': [t.to_dict() for t in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200

@transactions_bp.route('/transactions/<uuid:transaction_id>', methods=['PATCH'])
@jwt_required
def update_transaction(transaction_id):
    """Update a transaction's fields."""
    t = Transaction.query.filter_by(id=transaction_id, user_id=g.current_user_id, deleted_at=None).first()
    if not t:
        return jsonify({'error': 'Transacción no encontrada'}), 404
        
    data = request.get_json() or {}
    changes = {}
    
    if 'amount' in data and float(data['amount']) != float(t.amount):
        changes['amount'] = {'old': float(t.amount), 'new': float(data['amount'])}
        t.amount = data['amount']
        
    if 'description' in data and data['description'] != t.description:
        changes['description'] = {'old': t.description, 'new': data['description']}
        t.description = data['description']
        
    if 'merchant' in data and data['merchant'] != t.merchant:
        changes['merchant'] = {'old': t.merchant, 'new': data['merchant']}
        t.merchant = data['merchant']
        
    # Categories can also be updated here
    
    if changes:
        audit_log = AuditLog(
            user_id=g.current_user_id,
            transaction_id=t.id,
            action='UPDATE',
            changes=changes
        )
        db.session.add(audit_log)
        db.session.commit()
        
    return jsonify(t.to_dict()), 200

@transactions_bp.route('/transactions/<uuid:transaction_id>', methods=['DELETE'])
@jwt_required
def delete_transaction(transaction_id):
    """Soft-delete a transaction."""
    t = Transaction.query.filter_by(id=transaction_id, user_id=g.current_user_id, deleted_at=None).first()
    if not t:
        return jsonify({'error': 'Transacción no encontrada'}), 404
        
    t.soft_delete()
    
    audit_log = AuditLog(
        user_id=g.current_user_id,
        transaction_id=t.id,
        action='DELETE',
        changes={'deleted_at': {'old': None, 'new': t.deleted_at.isoformat()}}
    )
    db.session.add(audit_log)
    db.session.commit()
    
    return jsonify({'message': 'Transacción eliminada'}), 200

