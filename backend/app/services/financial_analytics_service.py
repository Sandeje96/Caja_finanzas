"""
services/financial_analytics_service.py

Handles natural language responses for financial queries using Python templates.
"""
from datetime import date
from app.services.financial_summary_service import FinancialSummaryService
from app.repositories.transaction_repository import TransactionRepository

class FinancialAnalyticsService:
    def __init__(self):
        self.summary_service = FinancialSummaryService()
        self.transaction_repo = TransactionRepository()

    def handle_query(self, user_id: str, intent: str, entities: dict) -> str:
        today = date.today()
        month = entities.get('month') or today.month
        year = today.year
        
        # Helper formatting
        def fmt(amount: float) -> str:
            return f"${float(amount):,.0f}".replace(',', '.')
            
        months = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        month_name = months[month] if 1 <= month <= 12 else str(month)
            
        if intent == 'QUERY_MONTH_EXPENSES':
            summary = self.summary_service.get_monthly_summary(user_id, year, month)
            return f"Gastaste {fmt(summary['expense'])} durante {month_name}."
            
        elif intent == 'QUERY_MONTH_INCOME':
            summary = self.summary_service.get_monthly_summary(user_id, year, month)
            return f"Ingresaste {fmt(summary['income'])} durante {month_name}."
            
        elif intent == 'QUERY_BALANCE':
            balance = self.summary_service.get_current_balance(user_id)
            if balance >= 0:
                return f"Tu balance actual (dinero disponible) es de {fmt(balance)}."
            else:
                return f"Tu balance actual es negativo: {fmt(balance)}."
                
        elif intent == 'QUERY_CATEGORY_EXPENSES':
            cat = entities.get('category')
            if not cat:
                return "¿En qué categoría te gustaría saber cuánto gastaste?"
            total = self.transaction_repo.get_category_expense_total(user_id, cat, year, month)
            return f"Gastaste {fmt(total)} en {cat} durante {month_name}."
            
        elif intent == 'QUERY_TOP_CATEGORY':
            cats = self.summary_service.get_expenses_by_category(user_id, year, month)
            if not cats:
                return f"No tenés gastos registrados en {month_name}."
            top = cats[0]
            return f"Tu categoría con más gastos en {month_name} fue {top['category_name']}, con {fmt(top['total'])}."
            
        elif intent == 'QUERY_BIGGEST_EXPENSE':
            biggest = self.summary_service.get_biggest_expense(user_id, year, month)
            if not biggest:
                return f"No encontré gastos en {month_name}."
            return f"Tu gasto más grande en {month_name} fue de {fmt(biggest.amount)} en {biggest.category.name if biggest.category else 'Otros'} ({biggest.description or 'sin descripción'})."
            
        elif intent == 'QUERY_COMPARE_MONTHS':
            comp = self.summary_service.get_monthly_comparison(user_id)
            c_exp = comp['current']['expense']
            p_exp = comp['previous']['expense']
            pct = comp['expense_change_pct']
            
            c_month = months[comp['current']['month']]
            p_month = months[comp['previous']['month']]
            
            reply = f"{c_month}: {fmt(c_exp)}\n{p_month}: {fmt(p_exp)}\n\n"
            if pct > 0:
                reply = "Sí.\n\n" + reply + f"Gastaste un {pct:.1f}% más."
            elif pct < 0:
                reply = "No.\n\n" + reply + f"Gastaste un {abs(pct):.1f}% menos."
            else:
                reply += "Gastaste exactamente lo mismo."
            return reply
            
        elif intent == 'QUERY_DATE_EXPENSES':
            q_date = entities.get('date')
            if not q_date:
                q_date = date.today().isoformat()
            
            try:
                dt = date.fromisoformat(q_date)
            except ValueError:
                dt = date.today()
                
            txs = self.transaction_repo.get_transactions_by_date(user_id, dt)
            expenses = [t for t in txs if t.type == 'expense']
            
            if not expenses:
                return f"No registraste ningún gasto el {dt.strftime('%d/%m/%Y')}."
                
            total = sum(t.amount for t in expenses)
            reply = f"El {dt.strftime('%d/%m/%Y')} gastaste un total de {fmt(total)}:\n\n"
            for t in expenses[:10]:
                cat = t.category.name if t.category else 'Otros'
                reply += f"• {fmt(t.amount)} en {cat}\n"
            
            if len(expenses) > 10:
                reply += f"\n(Y {len(expenses)-10} gastos más...)"
            return reply

        return "Lo siento, no puedo responder a esa consulta en este momento."
