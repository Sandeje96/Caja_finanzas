"""
api/auth.py — Dashboard authentication endpoints.

POST /api/auth/login    — Login with email + password → access + refresh tokens
POST /api/auth/refresh  — Refresh access token using refresh token
POST /api/auth/logout   — Revoke refresh token
GET  /api/auth/me       — Get current authenticated user profile

TODO: Implement in Sprint 6 (after AuthService is complete).
"""
import logging

from flask import Blueprint, jsonify

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate and return JWT tokens."""
    # TODO: Sprint 6
    return jsonify({'error': 'Not implemented yet — Sprint 6'}), 501


@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    """Refresh the access token."""
    # TODO: Sprint 6
    return jsonify({'error': 'Not implemented yet — Sprint 6'}), 501


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Revoke the refresh token."""
    # TODO: Sprint 6
    return jsonify({'error': 'Not implemented yet — Sprint 6'}), 501


@auth_bp.route('/me', methods=['GET'])
def me():
    """Return current user profile (requires valid access token)."""
    # TODO: Sprint 6
    return jsonify({'error': 'Not implemented yet — Sprint 6'}), 501
