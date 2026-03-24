from sqlalchemy import Column, Integer, String, DateTime
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "app_users" # Matches your preferred table name
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100))
    email = Column(String(100), unique=True, index=True)
    phone = Column(String(20), nullable=True)
    password = Column(String(100))
    role = Column(String(50), nullable=True)
    otp = Column(String(10), nullable=True)
    house_number = Column(String(100), nullable=True)
    street = Column(String(100), nullable=True)
    area = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    pincode = Column(String(20), nullable=True)
    landmark = Column(String(100), nullable=True)
    latitude = Column(String(50), nullable=True)
    longitude = Column(String(50), nullable=True)

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True, index=True)
    customer_email = Column(String(100))
    customer_name = Column(String(100))
    technician_id = Column(Integer, nullable=True)
    technician_email = Column(String(100))
    technician_name = Column(String(100))
    service_name = Column(String(100))
    address = Column(String(255))
    date = Column(String(50))
    time = Column(String(50))
    description = Column(String(255))
    status = Column(String(50), default="Pending")
    cost = Column(String(50), nullable=True)
    work_photo_url = Column(String(255), nullable=True)
    payment_status = Column(String(50), default="Pending")
    razorpay_order_id = Column(String(100), nullable=True)
    rating_value = Column(Integer, nullable=True)
    rating_comment = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.now)

class CustomerProfile(Base):
    __tablename__ = "customer_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, index=True)
    wallet_balance = Column(String(50), default="₹250.00")
    language = Column(String(50), default="English (US)")
    profile_pic_url = Column(String(255), nullable=True)

class TechnicianProfile(Base):
    __tablename__ = "technician_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, index=True)
    skills = Column(String(255), default="Primary: Electrician (+4 others)")
    experience = Column(String(100), nullable=True)
    service_radius = Column(String(100), default="Current Range: 15 miles")
    working_hours = Column(String(100), default="9:00 AM - 6:00 PM (Mon-Sat)")
    verification_status = Column(String(100), default="pending")
    payout_settings = Column(String(100), default="Next Payout: Feb 20, 2026")
    is_online = Column(String(50), default="true")
    rating = Column(String(50), default="5.0")
    profile_pic_url = Column(String(255), nullable=True)

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    sender_email = Column(String(100), index=True)
    receiver_email = Column(String(100), index=True)
    message = Column(String(500))
    timestamp = Column(String(50))
    status = Column(String(20), default="sent")

class TechnicianDocument(Base):
    __tablename__ = "technician_documents"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    doc_type = Column(String(100)) # ID, Certificate, Work Photo
    file_url = Column(String(255))
    uploaded_at = Column(DateTime, default=datetime.now)
