"""
utils/helpers.py — General-purpose utility functions.
"""
from datetime import date, datetime
from typing import Any


def paginate_response(pagination, items_key: str = 'items') -> dict:
    """
    Convert a Flask-SQLAlchemy Pagination object into a standard API response dict.

    Args:
        pagination: SQLAlchemy Pagination object (from .paginate())
        items_key: Key name for the items list in the response

    Returns:
        {
            'items': [...],
            'total': int,
            'page': int,
            'per_page': int,
            'pages': int,
            'has_next': bool,
            'has_prev': bool,
        }
    """
    return {
        items_key:  [item.to_dict() for item in pagination.items],
        'total':    pagination.total,
        'page':     pagination.page,
        'per_page': pagination.per_page,
        'pages':    pagination.pages,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev,
    }


def success_response(data: Any = None, message: str = None, status: int = 200) -> tuple:
    """
    Build a standard success JSON response.

    Returns:
        (response_dict, http_status_code)
    """
    payload = {'success': True}
    if message:
        payload['message'] = message
    if data is not None:
        payload['data'] = data
    return payload, status


def error_response(message: str, status: int = 400, details: Any = None) -> tuple:
    """
    Build a standard error JSON response.

    Returns:
        (response_dict, http_status_code)
    """
    payload = {'success': False, 'error': message}
    if details:
        payload['details'] = details
    return payload, status


def normalize_phone(phone: str) -> str:
    """
    Normalize a phone number to E.164 format.
    WhatsApp sends numbers without '+', e.g., '5491112345678'.
    We store them with '+', e.g., '+5491112345678'.
    """
    phone = phone.strip().replace(' ', '')
    if not phone.startswith('+'):
        phone = f'+{phone}'
    return phone


def current_month_year() -> tuple[int, int]:
    """Return (year, month) for the current date."""
    today = date.today()
    return today.year, today.month


def format_currency(amount: float, currency: str = 'ARS') -> str:
    """
    Format a number as a currency string.

    Examples:
        format_currency(18000)     → '$ 18.000,00'
        format_currency(1500.50)   → '$ 1.500,50'
    """
    # Argentine locale: period as thousands separator, comma as decimal
    formatted = f"{amount:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    return f"$ {formatted}"


def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert a value to float, returning default on failure."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
