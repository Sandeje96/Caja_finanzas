"""
api/dashboard.py — Dashboard summary and statistics endpoints.

GET /api/dashboard/summary  — Balance, income, expenses for current month
GET /api/dashboard/stats    — Data for charts (category breakdown, monthly trend)
"""
import logging
from flask import Blueprint, jsonify, request, g
from app.utils.decorators import jwt_required
from app.services.financial_summary_service import FinancialSummaryService
from datetime import date

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__)
summary_service = FinancialSummaryService()

@dashboard_bp.route('/dashboard/summary', methods=['GET'])
@jwt_required
def get_summary():
    """
    Financial summary for the home page.
    Returns balance, monthly income, monthly expenses.
    """
    today = date.today()
    summary = summary_service.get_monthly_summary(str(g.current_user_id), today.year, today.month)
    return jsonify(summary), 200


@dashboard_bp.route('/dashboard/stats', methods=['GET'])
@jwt_required
def get_stats():
    """
    Statistics data for Recharts graphs.
    Returns category breakdown, monthly comparison, top expenses.
    """
    today = date.today()
    cats = summary_service.get_expenses_by_category(str(g.current_user_id), today.year, today.month)
    
    # We could implement a 6-month historical data method here. For MVP we'll just return the current month breakdown
    return jsonify({
        'categories': cats,
        'monthly': summary_service.get_monthly_comparison(str(g.current_user_id))
    }), 200
