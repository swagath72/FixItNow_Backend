
from database import SessionLocal
import models

def check_techs():
    db = SessionLocal()
    techs = db.query(models.User).filter(models.User.role == "Technician").all()
    print(f"Found {len(techs)} technicians:")
    for t in techs:
        profile = db.query(models.TechnicianProfile).filter(models.TechnicianProfile.user_id == t.id).first()
        print(f"ID={t.id}, Name={t.full_name}, Email={t.email}, Role={t.role}")
        if profile:
            print(f"  Profile: Skills={profile.skills}, Exp={profile.experience}, Online={profile.is_online}")
        else:
            print("  No Profile found")
    db.close()

if __name__ == "__main__":
    check_techs()
