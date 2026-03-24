
import database, models
db = database.SessionLocal()
users = db.query(models.User).all()
for u in users:
    print(f"ID: {u.id}, Name: {u.full_name}, Email: '{u.email}', Role: {u.role}")
db.close()
