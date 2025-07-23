import os
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.models.user import User
from app.core.config import settings
from passlib.context import CryptContext

# Load .env
load_dotenv()

# DB setup
engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def main():
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")
    if not admin_email or not admin_password:
        print("ADMIN_EMAIL and ADMIN_PASSWORD must be set in .env")
        return
    session = SessionLocal()
    try:
        existing = session.query(User).filter(User.email == admin_email).first()
        if existing:
            if existing.is_admin:
                print(f"Admin user already exists: {admin_email}")
            else:
                existing.is_admin = True
                session.commit()
                print(f"User {admin_email} promoted to admin.")
            return
        hashed = pwd_context.hash(admin_password)
        admin = User(
            name="Admin",
            email=admin_email,
            password_hash=hashed,
            is_admin=True
        )
        session.add(admin)
        session.commit()
        print(f"Admin user created: {admin_email}")
    except Exception as e:
        session.rollback()
        print(f"Error creating admin: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    main() 