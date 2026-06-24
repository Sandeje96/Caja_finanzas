import pytest
from datetime import date
from app.models.transaction import Transaction
from app.models.category import Category
from app.services.financial_summary_service import FinancialSummaryService
from app.services.financial_analytics_service import FinancialAnalyticsService
from app.extensions import db

from app.models.user import User

@pytest.fixture
def financial_data(app):
    with app.app_context():
        # Clean up any existing
        Transaction.query.delete()
        Category.query.delete()
        User.query.delete()
        
        test_user = User(phone='+5491112345678')
        db.session.add(test_user)
        db.session.commit()
        
        cat1 = Category(name='Combustible', color='#ff0000', icon='gas')
        cat2 = Category(name='Supermercado', color='#00ff00', icon='cart')
        db.session.add_all([cat1, cat2])
        db.session.commit()
        
        t1 = Transaction(user_id=test_user.id, amount=95000, type='expense', category_id=cat1.id, transaction_date=date(2026, 6, 10))
        t2 = Transaction(user_id=test_user.id, amount=15000, type='expense', category_id=cat1.id, transaction_date=date(2026, 6, 15))
        t3 = Transaction(user_id=test_user.id, amount=50000, type='expense', category_id=cat2.id, transaction_date=date(2026, 6, 5))
        t4 = Transaction(user_id=test_user.id, amount=850000, type='income', transaction_date=date(2026, 6, 1))
        
        # Previous month
        t5 = Transaction(user_id=test_user.id, amount=100000, type='expense', category_id=cat1.id, transaction_date=date(2026, 5, 10))
        
        db.session.add_all([t1, t2, t3, t4, t5])
        db.session.commit()
        
        return test_user.id

def test_financial_summary_totals(financial_data, app):
    with app.app_context():
        service = FinancialSummaryService()
        
        # June 2026
        summary = service.get_monthly_summary(financial_data, 2026, 6)
        assert summary['income'] == 850000
        assert summary['expense'] == 160000
        assert summary['balance'] == 690000
        
        # May 2026
        summary_may = service.get_monthly_summary(financial_data, 2026, 5)
        assert summary_may['expense'] == 100000

def test_financial_analytics_responses(financial_data, app, monkeypatch):
    import datetime
    
    # Mock date to be June 2026
    class MockDate(datetime.date):
        @classmethod
        def today(cls):
            return cls(2026, 6, 24)
            
    monkeypatch.setattr('app.services.financial_analytics_service.date', MockDate)
    
    with app.app_context():
        service = FinancialAnalyticsService()
        
        reply1 = service.handle_query(financial_data, 'QUERY_MONTH_EXPENSES', {'month': 6})
        assert "Gastaste $160.000 durante Junio." in reply1
        
        reply2 = service.handle_query(financial_data, 'QUERY_CATEGORY_EXPENSES', {'month': 6, 'category': 'Combustible'})
        assert "Gastaste $110.000 en Combustible durante Junio." in reply2
        
        reply3 = service.handle_query(financial_data, 'QUERY_TOP_CATEGORY', {'month': 6})
        assert "Combustible" in reply3
        assert "$110.000" in reply3
        
        reply4 = service.handle_query(financial_data, 'QUERY_BIGGEST_EXPENSE', {'month': 6})
        assert "$95.000" in reply4
        assert "Combustible" in reply4
