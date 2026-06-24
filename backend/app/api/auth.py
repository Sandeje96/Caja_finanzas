"""
api/auth.py — Dashboard authentication endpoints.

POST /api/auth/login    — Request OTP via WhatsApp
POST /api/auth/verify   — Submit OTP, get access token
GET  /api/auth/me       — Get current authenticated user profile
"""
import logging
from flask import Blueprint, jsonify, request
from app.services.auth_service import AuthService
from app.models.user import User

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)
auth_service = AuthService()

@auth_bp.route('/login', methods=['POST'])
def login():
    """Request OTP via WhatsApp."""
    data = request.get_json() or {}
    phone = data.get('phone')
    if not phone:
        return jsonify({'error': 'Se requiere número de teléfono.'}), 400
        
    success = auth_service.request_otp(phone)
    if success:
        return jsonify({'message': 'Código enviado por WhatsApp.'}), 200
    else:
        return jsonify({'error': 'Error al enviar código.'}), 500

@auth_bp.route('/verify', methods=['POST'])
def verify():
    """Submit OTP and receive JWT."""
    data = request.get_json() or {}
    phone = data.get('phone')
    otp_code = data.get('otp_code')
    
    if not phone or not otp_code:
        return jsonify({'error': 'Faltan datos.'}), 400
        
    try:
        result = auth_service.verify_otp(phone, otp_code)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 401

@auth_bp.route('/me', methods=['GET'])
def me():
    """Return current user profile."""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Token no proporcionado.'}), 401
        
    token = auth_header.split(' ')[1]
    try:
        claims = auth_service.validate_access_token(token)
        user = User.query.get(claims['user_id'])
        if not user:
            return jsonify({'error': 'Usuario no encontrado.'}), 404
        return jsonify(user.to_public_dict()), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 401

