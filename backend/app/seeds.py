"""
seeds.py — Initial database seed data.

Run via Flask CLI:
    flask seed-db

Or from Python (inside app context):
    from app.seeds import seed_categories
    seed_categories()
"""
import logging

from app.extensions import db
from app.models.category import Category

logger = logging.getLogger(__name__)

# ─── System categories ─────────────────────────────────────────────────────────
# user_id = None  →  global categories available to all users
# is_system = True  →  cannot be edited or deleted by users

SYSTEM_CATEGORIES: list[dict] = [
    # ── Expenses ──────────────────────────────────────────────────────────────
    {'name': 'Supermercado',    'type': 'expense', 'icon': '🛒', 'color': '#4CAF50'},
    {'name': 'Combustible',     'type': 'expense', 'icon': '⛽', 'color': '#FF5722'},
    {'name': 'Servicios',       'type': 'expense', 'icon': '💡', 'color': '#FFC107'},
    {'name': 'Internet',        'type': 'expense', 'icon': '📶', 'color': '#2196F3'},
    {'name': 'Telefonía',       'type': 'expense', 'icon': '📱', 'color': '#9C27B0'},
    {'name': 'Alquiler',        'type': 'expense', 'icon': '🏠', 'color': '#795548'},
    {'name': 'Expensas',        'type': 'expense', 'icon': '🏢', 'color': '#607D8B'},
    {'name': 'Salud',           'type': 'expense', 'icon': '🏥', 'color': '#F44336'},
    {'name': 'Farmacia',        'type': 'expense', 'icon': '💊', 'color': '#E91E63'},
    {'name': 'Restaurante',     'type': 'expense', 'icon': '🍽️', 'color': '#FF9800'},
    {'name': 'Educación',       'type': 'expense', 'icon': '📚', 'color': '#3F51B5'},
    {'name': 'Impuestos',       'type': 'expense', 'icon': '🏛️', 'color': '#9E9E9E'},
    {'name': 'Transporte',      'type': 'expense', 'icon': '🚌', 'color': '#00BCD4'},
    {'name': 'Entretenimiento', 'type': 'expense', 'icon': '🎬', 'color': '#673AB7'},
    {'name': 'Mascotas',        'type': 'expense', 'icon': '🐾', 'color': '#FF8A65'},
    {'name': 'Indumentaria',    'type': 'expense', 'icon': '👕', 'color': '#26A69A'},
    # ── Income ────────────────────────────────────────────────────────────────
    {'name': 'Sueldo',              'type': 'income', 'icon': '💼', 'color': '#66BB6A'},
    {'name': 'Freelance',           'type': 'income', 'icon': '💻', 'color': '#42A5F5'},
    {'name': 'Alquiler Cobrado',    'type': 'income', 'icon': '🏡', 'color': '#26C6DA'},
    {'name': 'Inversiones',         'type': 'income', 'icon': '📈', 'color': '#FFCA28'},
    # ── Both ──────────────────────────────────────────────────────────────────
    {'name': 'Otros', 'type': 'both', 'icon': '📦', 'color': '#BDBDBD'},
]


def seed_categories() -> None:
    """Insert system categories if they don't already exist."""
    existing_count = Category.query.filter_by(is_system=True, user_id=None).count()

    if existing_count > 0:
        logger.info(f"[Seed] Categories already seeded ({existing_count} found). Skipping.")
        print(f"ℹ️  Categories already seeded ({existing_count} found). Skipping.")
        return

    for cat_data in SYSTEM_CATEGORIES:
        category = Category(
            name=cat_data['name'],
            type=cat_data['type'],
            icon=cat_data['icon'],
            color=cat_data['color'],
            is_system=True,
            user_id=None,
        )
        db.session.add(category)

    db.session.commit()
    count = len(SYSTEM_CATEGORIES)
    logger.info(f"[Seed] Seeded {count} system categories.")
    print(f"✅ Seeded {count} system categories.")
