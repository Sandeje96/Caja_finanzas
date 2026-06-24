"""
services/auth_service.py — Dashboard authentication via WhatsApp OTP.

Strategy: JWT with short-lived access tokens.
- User requests OTP via their WhatsApp number.
- OTP is sent via WhatsApp.
- User submits OTP to get a 24-hour access token.
"""
import logging
import random
import string
from datetime import datetime, timedelta, timezone
import jwt
from flask import current_app

from app.extensions import db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.whatsapp_service import WhatsAppService
from app.utils.helpers import normalize_phone

logger = logging.getLogger(__name__)

class AuthService:
    """Handles JWT-based authentication using OTP via WhatsApp."""

    def __init__(self):
        self.user_repo = UserRepository()
        self.whatsapp_service = WhatsAppService()

    def request_otp(self, phone: str) -> bool:
        """
        Generate a 6-digit OTP and send it via WhatsApp.
        Returns True if successful, False if user not found.
        """
        normalized_phone = normalize_phone(phone)
        user, _ = self.user_repo.find_or_create_by_phone(normalized_phone)
        
        # Generate 6 digit code
        otp_code = ''.join(random.choices(string.digits, k=6))
        otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        
        user.otp_code = otp_code
        user.otp_expires_at = otp_expires_at
        db.session.commit()
        
        message = f"🔑 Tu código de acceso para el Dashboard de Finanzas es: *{otp_code}*\n\nEste código expira en 10 minutos. Si no solicitaste este código, ignora este mensaje."
        
        try:
            self.whatsapp_service.send_text_message(user.phone, message)
            logger.info(f"[AuthService] OTP sent to {user.phone}")
            return True
        except Exception as e:
            logger.error(f"[AuthService] Error sending OTP to {user.phone}: {e}")
            return False

    def verify_otp(self, phone: str, otp_code: str) -> dict:
        """
        Verify the OTP and return a JWT access token.
        Raises ValueError if invalid or expired.
        """
        normalized_phone = normalize_phone(phone)
        user = User.query.filter_by(phone=normalized_phone).first()
        
        if not user:
            raise ValueError("Usuario no encontrado.")
            
        if not user.otp_code or user.otp_code != otp_code:
            raise ValueError("Código incorrecto.")
            
        if not user.otp_expires_at or user.otp_expires_at < datetime.now(timezone.utc):
            raise ValueError("El código ha expirado.")
            
        # Success - Clear OTP
        user.otp_code = None
        user.otp_expires_at = None
        db.session.commit()
        
        # Generate JWT
        secret = current_app.config.get('JWT_SECRET_KEY', 'dev-jwt-secret')
        payload = {
            'user_id': str(user.id),
            'phone': user.phone,
            'exp': datetime.now(timezone.utc) + timedelta(hours=24)
        }
        
        token = jwt.encode(payload, secret, algorithm='HS256')
        
        return {
            'access_token': token,
            'user': user.to_public_dict()
        }

    def validate_access_token(self, token: str) -> dict:
        """
        Validate an access token and return its claims.
        """
        secret = current_app.config.get('JWT_SECRET_KEY', 'dev-jwt-secret')
        try:
            return jwt.decode(token, secret, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise ValueError("El token ha expirado.")
        except jwt.InvalidTokenError:
            raise ValueError("Token inválido.")

