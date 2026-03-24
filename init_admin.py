from database import SessionLocal
from models import User

def init_admin():
    db = SessionLocal()
    try:
        # Check if admin already exists
        admin = db.query(User).filter(User.email == "admin@fixitnow.com").first()
        if admin:
            print("Admin already exists. Updating role and password...")
            admin.role = "admin"
            admin.password = "admin123"
            admin.full_name = "System Admin"
        else:
            print("Creating new admin user...")
            admin = User(
                email="admin@fixitnow.com",
                password="admin123",
                full_name="System Admin",
                role="admin",
                phone="0000000000"
            )
            db.add(admin)
        
        db.commit()
        print("Admin user initialized successfully!")
    except Exception as e:
        print(f"Error initializing admin: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_admin()
