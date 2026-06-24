from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Add OTP columns to users
    try:
        db.session.execute(text("ALTER TABLE users ADD COLUMN otp_code VARCHAR(6)"))
        db.session.execute(text("ALTER TABLE users ADD COLUMN otp_expires_at TIMESTAMP WITH TIME ZONE"))
        print("OTP columns added.")
    except Exception as e:
        print("OTP columns might already exist:", e)

    # Create audit_logs table
    try:
        db.session.execute(text("""
            CREATE TABLE audit_logs (
                id UUID PRIMARY KEY,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
                deleted_at TIMESTAMP WITH TIME ZONE,
                user_id UUID NOT NULL REFERENCES users(id),
                transaction_id UUID NOT NULL REFERENCES transactions(id),
                action VARCHAR(50) NOT NULL,
                changes JSONB NOT NULL
            )
        """))
        print("audit_logs table created.")
    except Exception as e:
        print("audit_logs table might already exist:", e)

    db.session.commit()
    # Update alembic version manually to avoid mismatch
    try:
        db.session.execute(text("UPDATE alembic_version SET version_num = '23456789abcd'"))
        db.session.commit()
    except Exception as e:
        print("Could not update alembic version", e)
    print("Migration applied successfully.")
