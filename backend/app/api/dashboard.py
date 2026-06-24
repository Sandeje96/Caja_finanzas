"""
api/dashboard.py — Dashboard summary and statistics endpoints.

GET /api/dashboard/summary  — Balance, income, expenses for current month
GET /api/dashboard/stats    — Data for charts (category breakdown, monthly trend)
"""
import logging

from flask import Blueprint, jsonify

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard/summary', methods=['GET'])
def get_summary():
    """
    Financial summary for the home page.
    Returns balance, monthly income, monthly expenses, transaction count.
    """
    # TODO: Sprint 5 (uses FinancialSummaryService)
    return jsonify({'error': 'Not implemented yet — Sprint 5'}), 501


@dashboard_bp.route('/dashboard/stats', methods=['GET'])
def get_stats():
    """
    Statistics data for Recharts graphs.
    Returns category breakdown, monthly comparison, top expenses.
    """
    # TODO: Sprint 5
    return jsonify({'error': 'Not implemented yet — Sprint 5'}), 501
