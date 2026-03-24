import database, models
from sqlalchemy import func
db = database.SessionLocal()
tups = db.query(models.User).filter(models.User.email.ilike('%ravi%')).all()
for u in tups:
    print(f"User ID: {u.id}, Name: {u.full_name}, Email: {u.email}")
    bb = db.query(models.Booking).filter(func.lower(models.Booking.technician_email) == u.email.lower()).all()
    print(f"  Bookings for {u.email}: {len(bb)}")
    for b in bb:
        print(f"    Booking ID: {b.id}, Status: {b.status}, Cost: {b.cost}")
db.close()
