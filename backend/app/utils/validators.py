"""
utils/validators.py — Input validation helpers.

Used by API endpoints to validate request data before delegating to services.
Raise ValueError for invalid input; endpoints convert to 400 responses.
"""
import re
from decimal import Decimal, InvalidOperation


# E.164 phone number pattern: +[country][number] (7–15 digits)
PHONE_E164_RE = re.compile(r'^\+[1-9]\d{6,14}$')

# Hex color: #RRGGBB
HEX_COLOR_RE = re.compile(r'^#[0-9A-Fa-f]{6}$')


def validate_phone_e164(phone: str) -> str:
    """
    Validate and normalize a phone number to E.164 format.
    Raises ValueError if invalid.
    """
    if not phone:
        raise ValueError("El número de teléfono es requerido.")
    phone = phone.strip().replace(' ', '')
    if not PHONE_E164_RE.match(phone):
        raise ValueError(
            f"Número de teléfono inválido: '{phone}'. "
            "Use formato E.164 (ej: +5491112345678)."
        )
    return phone


def validate_amount(value) -> Decimal:
    """
    Validate a financial amount.
    Must be a positive number with up to 2 decimal places.
    Raises ValueError if invalid.
    """
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"Monto inválido: '{value}'. Debe ser un número positivo.")

    if amount <= 0:
        raise ValueError("El monto debe ser mayor a cero.")

    # Round to 2 decimal places
    return amount.quantize(Decimal('0.01'))


def validate_transaction_type(type_value: str) -> str:
    """Validate transaction type. Raises ValueError if not one of the valid types."""
    valid = {'expense', 'income', 'transfer', 'adjustment'}
    if type_value not in valid:
        raise ValueError(
            f"Tipo de transacción inválido: '{type_value}'. "
            f"Valores válidos: {', '.join(sorted(valid))}."
        )
    return type_value


def validate_hex_color(color: str) -> str:
    """Validate a hex color string (#RRGGBB). Raises ValueError if invalid."""
    if color and not HEX_COLOR_RE.match(color):
        raise ValueError(f"Color inválido: '{color}'. Use formato #RRGGBB.")
    return color


def validate_email(email: str) -> str:
    """Basic email format validation. Raises ValueError if invalid."""
    if not email or '@' not in email or '.' not in email.split('@')[-1]:
        raise ValueError(f"Email inválido: '{email}'.")
    return email.lower().strip()


def validate_required(value, field_name: str):
    """Raise ValueError if value is None or empty string."""
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValueError(f"El campo '{field_name}' es requerido.")
    return value
