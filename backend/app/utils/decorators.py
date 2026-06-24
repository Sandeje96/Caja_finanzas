"""
utils/decorators.py — Flask route decorators.

Current decorators:
  - @jwt_required: Placeholder for Sprint 6 JWT authentication

Future decorators:
  - @rate_limit: Request rate limiting per user
  - @validate_json: JSON body validation
"""
import functools
import logging

from flask import jsonify, request

logger = logging.getLogger(__name__)


def jwt_required(f):
    """
    Decorator that requires a valid JWT access token.

    Usage:
        @app.route('/protected')
        @jwt_required
        def protected():
            return jsonify({'user_id': g.current_user_id})

    TODO: Implement in Sprint 6.
    Currently returns 501 to clearly signal the feature is not ready.
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        from flask import g
        from app.services.auth_service import AuthService
        from app.models.user import User
        
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Autenticación requerida. Token no proporcionado.'}), 401
            
        token = auth_header.split(' ')[1]
        try:
            auth_service = AuthService()
            claims = auth_service.validate_access_token(token)
            user = User.query.get(claims['user_id'])
            if not user:
                return jsonify({'error': 'Usuario no encontrado.'}), 404
            
            # Pass user to the route via g
            g.current_user = user
            g.current_user_id = user.id
        except ValueError as e:
            return jsonify({'error': str(e)}), 401
            
        return f(*args, **kwargs)
    return decorated


def validate_json(*required_fields):
    """
    Decorator that validates the presence of required JSON body fields.

    Usage:
        @app.route('/api/resource', methods=['POST'])
        @validate_json('amount', 'type')
        def create_resource():
            data = request.get_json()
            ...
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated(*args, **kwargs):
            data = request.get_json(silent=True)
            if data is None:
                return jsonify({'error': 'Request body must be valid JSON.'}), 400

            missing = [field for field in required_fields if field not in data]
            if missing:
                return jsonify({
                    'error': f"Missing required fields: {', '.join(missing)}"
                }), 400

            return f(*args, **kwargs)
        return decorated
    return decorator
