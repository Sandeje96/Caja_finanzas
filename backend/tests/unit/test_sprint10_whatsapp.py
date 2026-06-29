import pytest
from unittest.mock import patch, MagicMock
from app.services.webhook_processor import WebhookProcessor
from app.repositories.user_repository import UserRepository
from app.models.transaction import Transaction
from app.models.category import Category
from app.models.pending_action import PendingAction
from app.extensions import db

def make_text_payload(phone, text, msg_id="test_msg_id"):
    return {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": phone,
                                    "id": msg_id,
                                    "type": "text",
                                    "text": {"body": text}
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }

@pytest.fixture
def processor(app):
    with app.app_context():
        # Clean DB for each test
        db.drop_all()
        db.create_all()
        # Seed 'Otros' category which is required by TransactionService fallback
        cat = Category(name='Otros', type='both', is_system=True)
        db.session.add(cat)
        db.session.commit()
    return WebhookProcessor()

def mock_classify_intent(message, context, user_id, message_id):
    msg = message.lower()
    
    # 1. REGISTER_EXPENSE
    if "gasté" in msg and "ypf" in msg:
        return {
            "intent": "REGISTER_EXPENSE",
            "confidence": 0.95,
            "entities": {"amount": 18500, "merchant": "YPF", "category": "Combustible", "description": "Nafta"}
        }
    
    # 2. REGISTER_INCOME
    if "cobré" in msg and "sueldo" in msg:
        return {
            "intent": "REGISTER_INCOME",
            "confidence": 0.98,
            "entities": {"amount": 850000, "description": "Sueldo", "category": "Sueldo"}
        }
        
    # 3. Flujo conversacional (missing amount)
    if "cargué nafta ayer" in msg:
        return {
            "intent": "REGISTER_EXPENSE",
            "confidence": 0.90,
            "entities": {"merchant": "Estación de Servicio", "category": "Combustible", "description": "Nafta"}
        }
    if "3200" in msg:
        # Assuming the context helps AI understand it's the amount
        return {
            "intent": "REGISTER_EXPENSE",
            "confidence": 0.90,
            "entities": {"amount": 3200, "merchant": "Estación de Servicio", "category": "Combustible"}
        }
        
    # 4. Low confidence
    if "compré algo raro por 500" in msg:
        return {
            "intent": "REGISTER_EXPENSE",
            "confidence": 0.60,
            "entities": {"amount": 500, "description": "algo raro"}
        }
        
    return {"intent": "UNKNOWN", "confidence": 0.0, "entities": {}}


@patch('app.services.ai_service.AIService.classify_intent', side_effect=mock_classify_intent)
@patch('app.services.whatsapp_service.WhatsAppService.send_text_message')
def test_register_expense(mock_whatsapp, mock_ai, processor, app):
    with app.app_context():
        processor._process(make_text_payload("5491112345678", "Gasté 18.500 en YPF"))
        
        # Verify transaction
        t = Transaction.query.first()
        assert t is not None
        assert t.amount == 18500
        assert t.type == 'expense'
        assert t.merchant == 'YPF'
        
        # Verify category mapping to fallback 'Otros'
        assert t.category.name == 'Otros'
        
        # Verify whatsapp message sent
        assert mock_whatsapp.call_count == 1
        reply = mock_whatsapp.call_args[0][1]
        assert "✅ Gasto registrado" in reply
        assert "18.500" in reply


@patch('app.services.ai_service.AIService.classify_intent', side_effect=mock_classify_intent)
@patch('app.services.whatsapp_service.WhatsAppService.send_text_message')
def test_register_income(mock_whatsapp, mock_ai, processor, app):
    with app.app_context():
        processor._process(make_text_payload("5491112345678", "Cobré sueldo 850000"))
        
        t = Transaction.query.first()
        assert t is not None
        assert t.amount == 850000
        assert t.type == 'income'
        
        assert mock_whatsapp.call_count == 1
        reply = mock_whatsapp.call_args[0][1]
        assert "✅ Ingreso registrado" in reply


@patch('app.services.ai_service.AIService.classify_intent', side_effect=mock_classify_intent)
@patch('app.services.whatsapp_service.WhatsAppService.send_text_message')
def test_conversational_fallback(mock_whatsapp, mock_ai, processor, app):
    with app.app_context():
        # First message missing amount
        processor._process(make_text_payload("5491112345678", "Cargué nafta ayer", "msg1"))
        
        # No transaction should be created yet
        assert Transaction.query.count() == 0
        
        # A pending action should be created
        pa = PendingAction.query.first()
        assert pa is not None
        assert pa.action_type == 'CONFIRM_EXPENSE'
        assert pa.payload_json['merchant'] == 'Estación de Servicio'
        
        # Should ask for amount
        reply = mock_whatsapp.call_args[0][1]
        assert "¿De cuánto fue" in reply
        
        # User provides amount
        processor._process(make_text_payload("5491112345678", "3200", "msg2"))
        
        # Transaction should now be created
        t = Transaction.query.first()
        assert t is not None
        assert t.amount == 3200


@patch('app.services.ai_service.AIService.classify_intent', side_effect=mock_classify_intent)
@patch('app.services.whatsapp_service.WhatsAppService.send_text_message')
def test_low_confidence_pending_action(mock_whatsapp, mock_ai, processor, app):
    with app.app_context():
        processor._process(make_text_payload("5491112345678", "compré algo raro por 500", "msg3"))
        
        assert Transaction.query.count() == 0
        
        pa = PendingAction.query.first()
        assert pa is not None
        assert pa.action_type == 'CONFIRM_EXPENSE'
        
        reply = mock_whatsapp.call_args[0][1]
        assert "⚠️ Por favor confirmá este gasto" in reply
        assert "Respondé OK para confirmar o NO para cancelar" in reply
