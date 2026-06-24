import pytest
from unittest.mock import patch, MagicMock
from app.services.ocr_service import OCRService
from app.services.pending_action_service import PendingActionService
from app.models.pending_action import PendingAction
from app.models.transaction import Transaction

@patch('app.services.ocr_service.OpenAI')
def test_ocr_success(mock_openai_class, app):
    mock_client = mock_openai_class.return_value
    
    mock_choice = MagicMock()
    mock_choice.message.content = '{"merchant": "Coto", "amount": 15000, "category": "Supermercado", "date": "2026-06-25", "confidence": 0.95}'
    
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.usage.prompt_tokens = 100
    mock_response.usage.completion_tokens = 50
    mock_client.chat.completions.create.return_value = mock_response

    app.config['OPENAI_API_KEY'] = 'test-key'
    with app.app_context():
        ocr = OCRService()
        data, conf = ocr.analyze_receipt_from_url("https://example.com/receipt.jpg", "user1", "msg1")
        
        assert data.get('merchant') == "Coto"
        assert data.get('amount') == 15000
        assert conf == 0.95

def test_pending_action_lifecycle(app):
    with app.app_context():
        from app.extensions import db
        from app.models.user import User
        user = User(phone="111111111")
        db.session.add(user)
        db.session.commit()
        
        svc = PendingActionService()
        
        # 1. Crear accion - pasamos str(user.id) y SQLAlchemy puede requerir UUID
        import uuid
        action = svc.create_action(user.id, 'CONFIRM_EXPENSE', {'amount': 1500, 'description': 'test', 'category': 'Otros'})
        assert action.status == 'pending'
        
        # 2. Get last active
        active = svc.get_last_active_action(user.id)
        assert active is not None
        assert active.id == action.id
        
        # 3. Resolver
        result = svc.resolve_last_action(user.id)
        assert result is not None
        assert result['action_type'] == 'CONFIRM_EXPENSE'
        assert result['transaction'] is not None
        
        t = result['transaction']
        assert t.amount == 1500
        
        assert action.status == 'confirmed'
        
        # 4. Cancelar
        action2 = svc.create_action(user.id, 'DELETE_TRANSACTION', {})
        res_cancel = svc.cancel_last_action(user.id)
        assert res_cancel is True
        assert action2.status == 'cancelled'
