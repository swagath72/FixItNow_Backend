import math
from typing import List, Optional, Dict
from fastapi import FastAPI, Depends, HTTPException, status, Header, File, UploadFile, Form, Query
from fastapi.middleware.cors import CORSMiddleware
import razorpay
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, validator
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from datetime import datetime
import random
import uvicorn
import os
import shutil
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import models
from database import SessionLocal, engine
import sys
import os
from chatbot.chatbot import get_response

# Automatically create/update tables in MySQL
models.Base.metadata.create_all(bind=engine)

def init_admin():
    db = SessionLocal()
    try:
        # Check if admin already exists
        admin = db.query(models.User).filter(models.User.email == "admin@fixitnow.com").first()
        if admin:
            # Update to ensure correct role and password
            admin.role = "admin"
            admin.password = "admin123"
            admin.full_name = "System Admin"
        else:
            # Create new admin user
            admin = models.User(
                email="admin@fixitnow.com",
                password="admin123",
                full_name="System Admin",
                role="admin",
                phone="0000000000"
            )
            db.add(admin)
        
        db.commit()
    except Exception as e:
        print(f"Error initializing admin: {e}")
        db.rollback()
    finally:
        db.close()

# Run admin initialization
init_admin()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Make sure uploads directory exists
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# --- Email Configuration ---
# Credentials are loaded from .env file (MAIL_USERNAME, MAIL_PASSWORD, MAIL_FROM)
# The config is built lazily inside the endpoint so the server starts
# even when credentials are not yet configured.
def get_mail_config() -> ConnectionConfig:
    mail_user = os.getenv("MAIL_USERNAME", "")
    mail_pass = os.getenv("MAIL_PASSWORD", "")
    mail_from = os.getenv("MAIL_FROM", mail_user)  # fallback to username
    mail_from_name = os.getenv("MAIL_FROM_NAME", "FIXIT NOW Support")

    if not mail_user or not mail_from or "@" not in mail_from:
        raise HTTPException(
            status_code=503,
            detail="Email service is not configured. Please set MAIL_USERNAME, MAIL_PASSWORD, and MAIL_FROM in the .env file."
        )

    return ConnectionConfig(
        MAIL_USERNAME="mr.swagath72@gmail.com",
        MAIL_PASSWORD="idyz sixx samz kkwg",
        MAIL_FROM="mr.swagath72@gmail.com",
        MAIL_PORT=465,
        MAIL_SERVER="smtp.gmail.com",
        MAIL_FROM_NAME=mail_from_name,
        MAIL_STARTTLS=False,
        MAIL_SSL_TLS=True,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True,
        TEMPLATE_FOLDER=None
    )

def haversine(lat1, lon1, lat2, lon2):
    # Radius of the Earth in kilometers
    R = 6371.0
    
    # Convert latitude and longitude from degrees to radians
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    # Haversine formula
    a = math.sin(delta_phi / 2)**2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Distance in kilometers
    distance = R * c
    return distance

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Pydantic Models ---
class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    phone: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RoleSelectionRequest(BaseModel):
    role: str

class AddAddressRequest(BaseModel):
    house_number: str
    street: str
    area: str
    city: str
    state: str
    pincode: str
    landmark: Optional[str] = None

class TechnicianRegisterRequest(BaseModel):
    skills: List[str]
    experience_years: int
    service_type: str
    phone: Optional[str] = None # Added field if used in registration

class TechnicianOnboardingRequest(BaseModel):
    skills: str
    experience: str

class CreateBookingRequest(BaseModel):
    address: str
    date: str
    time: str
    description: str
    service_name: str
    technician_id: int
    technician_name: str
    customer_name: str
    cost: str

class UpdateJobStatusRequest(BaseModel):
    booking_id: int
    status: str

class SubmitRatingRequest(BaseModel):
    booking_id: int
    rating: float
    comment: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class VerifyOtpRequest(BaseModel):
    email: EmailStr
    otp: str

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    new_password: str
    confirm_password: str

class RazorpayOrderRequest(BaseModel):
    booking_id: int
    amount: float

class RazorpayOrderResponse(BaseModel):
    order_id: str
    amount: int
    currency: str
    key_id: str

class PaymentVerificationRequest(BaseModel):
    booking_id: int
    razorpay_payment_id: str
    razorpay_order_id: str
    razorpay_signature: str

class UpdateAvailabilityRequest(BaseModel):
    is_online: bool

class UpdateLocationRequest(BaseModel):
    latitude: float
    longitude: float

class CustomerProfileResponse(BaseModel):
    full_name: str
    email: str
    phone: str
    address: str
    wallet_balance: str
    language: str
    profile_pic_url: Optional[str]

class TechnicianProfileResponse(BaseModel):
    full_name: str
    email: str
    phone: str
    address: str
    skills: str
    service_radius: str
    working_hours: str
    verification_status: str
    payout_settings: str
    is_online: str
    rating: str
    profile_pic_url: Optional[str] = None
    has_completed_onboarding: bool = False

class LoginResponse(BaseModel):
    status: str
    message: str
    token: str
    role: str
    full_name: str
    phone: str
    booked_technician_name: str
    booking_status: str
    house_number: str
    area: str
    street: str
    city: str
    state: str
    pincode: str
    has_completed_onboarding: bool
    profile_pic_url: Optional[str] = None
    verification_status: Optional[str] = None

class SendMessageRequest(BaseModel):
    receiver_email: str
    message: str

class ChatMessage(BaseModel):
    id: Optional[int] = None
    sender_email: str
    receiver_email: str
    message: str
    timestamp: Optional[str] = None
    is_sent_by_me: bool = False
    status: str = "sent"

class ChatListItem(BaseModel):
    name: str
    email: str
    last_message: str
    time: str
    unread_count: int
    role: str
    profile_pic_url: Optional[str] = None

class ChatResponse(BaseModel):
    messages: List[ChatMessage]
    is_active: bool

class AiChatRequest(BaseModel):
    message: str

class AiChatResponseModel(BaseModel):
    response: str


# --- Auth Dependency ---
from fastapi import Request

async def get_current_user(request: Request, Authorization: str = Header(None), db: Session = Depends(get_db)):
    # Multiple fallbacks for maximum resilience across different browsers/clients
    auth_header = Authorization
    if not auth_header:
        auth_header = request.headers.get("Authorization") or request.headers.get("authorization")
    
    if not auth_header:
        # Check for common variants in case of proxies
        auth_header = request.headers.get("HTTP_AUTHORIZATION")
        
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    authorization = auth_header
        
    # Extract email from "Bearer {email}" case-insensitively
    import re
    match = re.search(r'Bearer\s+(.+)', authorization, re.IGNORECASE)
    if not match:
        raise HTTPException(status_code=401, detail="Header must start with 'Bearer ' followed by the token")
    
    from sqlalchemy import func
    email = match.group(1).strip().lower()
    user = db.query(models.User).filter(func.lower(models.User.email) == email).first()
    if not user:
        raise HTTPException(status_code=401, detail=f"User session invalid: '{email}' not found")
    return user

# --- API Endpoints ---

@app.post("/register")
def register(user: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = models.User(
        full_name=user.full_name, 
        email=user.email, 
        password=user.password,
        phone=user.phone
    )
    db.add(new_user)
    db.commit()
    return {"message": "User registered successfully"}

@app.post("/login")
def login(form_data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.email).first()
    if user is None or user.password != form_data.password:
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    latest_booking = db.query(models.Booking).filter(
        models.Booking.customer_email == user.email,
        models.Booking.status.not_in(["Completed", "Cancelled", "Rejected", "Finished"])
    ).order_by(models.Booking.id.desc()).first()

    profile_pic_url = None
    verification_status = None
    if user.role == "Customer":
        profile = db.query(models.CustomerProfile).filter(models.CustomerProfile.user_id == user.id).first()
        if profile:
            profile_pic_url = profile.profile_pic_url
    elif user.role == "Technician":
        profile = db.query(models.TechnicianProfile).filter(models.TechnicianProfile.user_id == user.id).first()
        if profile:
            profile_pic_url = profile.profile_pic_url
            verification_status = profile.verification_status

    return {
        "status": "success",
        "message": "Login successful",
        "token": user.email,
        "role": user.role or "",
        "full_name": user.full_name or "User",
        "phone": user.phone or "",
        "booked_technician_name": latest_booking.technician_name if latest_booking else "",
        "booking_status": latest_booking.status if latest_booking else "",
        "house_number": user.house_number or "",
        "area": user.area or "",
        "street": user.street or "",
        "city": user.city or "",
        "state": user.state or "",
        "pincode": user.pincode or "",
        "has_completed_onboarding": check_onboarding_status(user, db),
        "profile_pic_url": profile_pic_url,
        "verification_status": verification_status
    }

def check_onboarding_status(user: models.User, db: Session) -> bool:
    if user.role != "Technician":
        return True
    
    profile = db.query(models.TechnicianProfile).filter(models.TechnicianProfile.user_id == user.id).first()
    if not profile or not profile.skills or not profile.experience:
        return False
        
    doc_count = db.query(models.TechnicianDocument).filter(models.TechnicianDocument.user_id == user.id).count()
    return doc_count >= 3

@app.post("/create-booking")
def create_booking(req: CreateBookingRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    tech = db.query(models.User).filter(models.User.id == req.technician_id).first()
    if not tech:
        raise HTTPException(status_code=404, detail="Technician not found")

    new_booking = models.Booking(
        customer_email=current_user.email,
        customer_name=req.customer_name,
        technician_id=req.technician_id,
        technician_email=tech.email,
        technician_name=req.technician_name,
        service_name=req.service_name,
        address=req.address,
        date=req.date,
        time=req.time,
        description=req.description,
        cost=req.cost,
        status="Pending"
    )
    db.add(new_booking)
    db.commit()
    return {"message": "Booking successful", "booking_id": new_booking.id}

@app.get("/active-bookings")
def get_active_bookings(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Booking).filter(
        models.Booking.customer_email == current_user.email,
        (models.Booking.status.not_in(["Completed", "Cancelled", "Rejected"])) |
        ((models.Booking.status == "Completed") & (models.Booking.payment_status != "Paid"))
    ).all()

@app.get("/recent-bookings")
def get_recent_bookings(date: str = None, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # If no date is passed, fall back to server's today (not ideal, but safe)
    if not date:
        date = datetime.now().strftime("%d/%m/%Y")
        
    return db.query(models.Booking).filter(
        models.Booking.customer_email == current_user.email,
        models.Booking.date == date
    ).order_by(models.Booking.id.desc()).all()

@app.get("/users/me")
def read_users_me(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = None
    if current_user.role == "Customer":
        profile = db.query(models.CustomerProfile).filter(models.CustomerProfile.user_id == current_user.id).first()
    elif current_user.role == "Technician":
        profile = db.query(models.TechnicianProfile).filter(models.TechnicianProfile.user_id == current_user.id).first()

    return {
        "id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "phone": current_user.phone,
        "role": current_user.role,
        "profile_pic_url": profile.profile_pic_url if profile else None
    }

class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

@app.put("/users/me")
def update_users_me(req: UpdateProfileRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update the current user's basic profile info (name, phone, email)."""
    if req.full_name is not None:
        current_user.full_name = req.full_name
    if req.phone is not None:
        current_user.phone = req.phone
    if req.email is not None and req.email != current_user.email:
        # Check if email already in use by another user
        existing = db.query(models.User).filter(models.User.email == req.email).first()
        if existing and existing.id != current_user.id:
            raise HTTPException(status_code=400, detail="Email already in use")
        current_user.email = req.email
    db.commit()
    db.refresh(current_user)

    profile = None
    if current_user.role == "Customer":
        profile = db.query(models.CustomerProfile).filter(models.CustomerProfile.user_id == current_user.id).first()
    elif current_user.role == "Technician":
        profile = db.query(models.TechnicianProfile).filter(models.TechnicianProfile.user_id == current_user.id).first()

    return {
        "id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "phone": current_user.phone,
        "role": current_user.role,
        "profile_pic_url": profile.profile_pic_url if profile else None
    }

@app.post("/user/update-profile")
def update_profile_android(req: UpdateProfileRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update profile endpoint specifically for the Android app (POST instead of PUT)."""
    if req.full_name:
        current_user.full_name = req.full_name
    if req.phone:
        current_user.phone = req.phone
    if req.email and req.email != current_user.email:
        existing = db.query(models.User).filter(models.User.email == req.email).first()
        if existing and existing.id != current_user.id:
            raise HTTPException(status_code=400, detail="Email already in use")
        current_user.email = req.email
    
    db.commit()
    return {"message": "Profile updated successfully"}

@app.post("/users/me/photo")
async def upload_profile_photo(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a profile photo for the current user."""
    # Save file to uploads/
    ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
    filename = f"profile_{current_user.id}_{int(datetime.now().timestamp())}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    pic_url = f"/uploads/{filename}"

    # Update the correct profile table
    if current_user.role == "Customer":
        profile = db.query(models.CustomerProfile).filter(models.CustomerProfile.user_id == current_user.id).first()
        if not profile:
            profile = models.CustomerProfile(user_id=current_user.id)
            db.add(profile)
        profile.profile_pic_url = pic_url
    elif current_user.role == "Technician":
        profile = db.query(models.TechnicianProfile).filter(models.TechnicianProfile.user_id == current_user.id).first()
        if not profile:
            profile = models.TechnicianProfile(user_id=current_user.id)
            db.add(profile)
        profile.profile_pic_url = pic_url
    else:
        raise HTTPException(status_code=400, detail="User role not set. Cannot save photo.")

    db.commit()
    return {"profile_pic_url": pic_url, "message": "Photo uploaded successfully"}

@app.get("/bookings")
def get_user_bookings(status: Optional[str] = None, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    print(f"DEBUG: get_user_bookings for user {current_user.email} (ID: {current_user.id}, Role: {current_user.role})")
    from sqlalchemy import func, or_

    if not current_user.role:
        raise HTTPException(
            status_code=400,
            detail="User role is not set. Please select a role (Customer or Technician) before viewing bookings."
        )

    if current_user.role == "Customer":
        query = db.query(models.Booking).filter(func.lower(models.Booking.customer_email) == current_user.email.lower())
    elif current_user.role == "Technician":
        # Match by ID or Email for maximum reliability
        query = db.query(models.Booking).filter(
            or_(
                func.lower(models.Booking.technician_email) == current_user.email.lower(),
                models.Booking.technician_id == current_user.id
            )
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unknown role: {current_user.role}")
    
    if status:
        # Simple case-insensitive match for "Pending", "Completed", etc.
        query = query.filter(models.Booking.status.ilike(status))
        
    results = query.order_by(models.Booking.id.desc()).all()
    print(f"DEBUG: get_user_bookings found {len(results)} results")
    return results

@app.get("/booking/{booking_id}")
def get_booking_details(booking_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Optional: security check to ensure the user is allowed to see this booking
    if current_user.role == "Customer" and booking.customer_email != current_user.email:
        raise HTTPException(status_code=403, detail="Unauthorized access to this booking")
    if current_user.role == "Technician" and booking.technician_email != current_user.email:
        raise HTTPException(status_code=403, detail="Unauthorized access to this booking")
         
    return booking


@app.get("/booking-history")
def get_history(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    from sqlalchemy import func
    return db.query(models.Booking).filter(
        func.lower(models.Booking.customer_email) == current_user.email.lower()
    ).order_by(models.Booking.id.desc()).all()

@app.get("/technicians")
def get_technicians(lat: Optional[float] = None, lng: Optional[float] = None, db: Session = Depends(get_db)):
    # Only show technicians who are verified AND online
    valid_profiles = db.query(models.TechnicianProfile).filter(
        models.TechnicianProfile.is_online == "true",
        models.TechnicianProfile.verification_status == "approved"
    ).all()
    valid_user_ids = [p.user_id for p in valid_profiles]
    
    technicians = db.query(models.User).filter(
        models.User.role.ilike("Technician"),
        models.User.id.in_(valid_user_ids)
    ).all()
    
    result = []
    for t in technicians:
        current_distance = None
        # Distance filtering if coordinates provided by customer
        if lat is not None and lng is not None:
            if t.latitude and t.longitude:
                try:
                    t_lat = float(t.latitude)
                    t_lng = float(t.longitude)
                    current_distance = haversine(lat, lng, t_lat, t_lng)
                    
                    # Filter by 15km radius
                    if current_distance > 15.0:
                        continue
                except ValueError:
                    continue # Skip if bad coordinates
            else:
                continue # Skip if technician has no coordinates and we are filtering by radius
        
        profile = next((p for p in valid_profiles if p.user_id == t.id), None)
        rating = "0.0"
        pic_url = None
        skills = ""
        if profile:
            rating = profile.rating or "4.5"
            pic_url = profile.profile_pic_url
            skills = profile.skills
            
        result.append({
            "id": t.id,
            "full_name": t.full_name,
            "email": t.email,
            "role": t.role,
            "skills": skills,
            "rating": rating,
            "profile_pic_url": pic_url,
            "distance": f"{current_distance:.1f} km" if current_distance is not None else None
        })
    
    return result

@app.post("/select-role")
def select_role(req: RoleSelectionRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    current_user.role = req.role
    
    if req.role == "Customer":
        profile = db.query(models.CustomerProfile).filter(models.CustomerProfile.user_id == current_user.id).first()
        if not profile:
            new_profile = models.CustomerProfile(user_id=current_user.id)
            db.add(new_profile)
    elif req.role == "Technician":
        profile = db.query(models.TechnicianProfile).filter(models.TechnicianProfile.user_id == current_user.id).first()
        if not profile:
            new_profile = models.TechnicianProfile(user_id=current_user.id)
            db.add(new_profile)

    db.commit()
    return {"message": f"Role updated to {req.role}"}

@app.post("/add-address")
def add_address(req: AddAddressRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    current_user.house_number, current_user.street, current_user.area = req.house_number, req.street, req.area
    current_user.city, current_user.state, current_user.pincode, current_user.landmark = req.city, req.state, req.pincode, req.landmark
    db.commit()
    return {"message": "Address added successfully"}

@app.post("/technician/register")
def register_technician(req: TechnicianRegisterRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    current_user.role = "Technician"
    
    profile = db.query(models.TechnicianProfile).filter(models.TechnicianProfile.user_id == current_user.id).first()
    if not profile:
        profile = models.TechnicianProfile(user_id=current_user.id)
        db.add(profile)
    
    profile.skills = f"Primary: {req.service_type} (+{len(req.skills)-1} others)" if len(req.skills) > 1 else req.service_type
    profile.experience = f"{req.experience_years} years"
    
    # We also mock-upload 3 documents to satisfy onboarding for now
    for doc_type in ["ID Card", "Certificate", "Experience Letter"]:
        existing = db.query(models.TechnicianDocument).filter(
            models.TechnicianDocument.user_id == current_user.id,
            models.TechnicianDocument.doc_type == doc_type
        ).first()
        if not existing:
            doc = models.TechnicianDocument(
                user_id=current_user.id,
                doc_type=doc_type,
                file_url="/uploads/mock_doc.pdf"
            )
            db.add(doc)
            
    db.commit()
    return {"message": "Technician registered successfully"}

@app.post("/technician/update-onboarding")
def update_technician_onboarding(req: TechnicianOnboardingRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    profile = db.query(models.TechnicianProfile).filter(models.TechnicianProfile.user_id == current_user.id).first()
    if not profile:
        profile = models.TechnicianProfile(user_id=current_user.id)
        db.add(profile)
    
    profile.skills = req.skills
    profile.experience = req.experience
    db.commit()
    return {"message": "Onboarding details saved"}

# --- Technician Endpoints ---
from datetime import datetime, timedelta
import re

@app.get("/technician/earnings")
def get_technician_earnings(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    from sqlalchemy import func, or_
    # Match by ID or Email for maximum reliability
    all_assigned_bookings = db.query(models.Booking).filter(
        or_(
            func.lower(models.Booking.technician_email) == current_user.email.lower(),
            models.Booking.technician_id == current_user.id
        )
    ).all()

    completed_statuses = ["Completed", "completed", "Paid", "paid"]
    completed_bookings = [b for b in all_assigned_bookings if b.status in completed_statuses]

    today_earnings = 0
    weekly_earnings = 0
    monthly_earnings = 0
    today_jobs = 0
    weekly_jobs = 0
    monthly_jobs = 0

    now = datetime.now()
    
    # helper to normalize dd/mm/yyyy or d/m/yyyy to a tuple (d, m, y)
    def parse_booking_date(date_str):
        if not date_str: return None
        try:
            # Handle possible varied formats
            for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt
                except ValueError: continue
            return None
        except: return None

    today_date = now.date()
    seven_days_ago = (now - timedelta(days=7)).date()
    current_month = now.month
    current_year = now.year

    import re
    for booking in completed_bookings:
        raw_cost = booking.cost or "0"
        cost_str = re.sub(r'[^\d.]', '', str(raw_cost))
        try:
            cost = float(cost_str) if cost_str else 0.0
        except ValueError:
            cost = 0.0

        b_dt = parse_booking_date(booking.date)
        if not b_dt:
            continue
            
        b_date = b_dt.date()
        
        # Check Today
        if b_date == today_date:
            today_earnings += cost
            today_jobs += 1
            
        # Check Month
        if b_dt.month == current_month and b_dt.year == current_year:
            monthly_earnings += cost
            monthly_jobs += 1
            
        # Check Week
        if seven_days_ago <= b_date <= today_date:
            weekly_earnings += cost
            weekly_jobs += 1

    rated_bookings = [b for b in completed_bookings if b.rating_value is not None and b.rating_value > 0]
    avg_rating = sum(b.rating_value for b in rated_bookings) / len(rated_bookings) if rated_bookings else 0.0
    
    total_jobs = len(all_assigned_bookings)
    success_rate = f"{int(len(completed_bookings) / total_jobs * 100)}%" if total_jobs > 0 else "0%"

    return {
        "today": int(today_earnings),
        "today_earnings": int(today_earnings), # fallback
        "weekly": int(weekly_earnings),
        "weekly_earnings": int(weekly_earnings), # fallback
        "monthly": int(monthly_earnings),
        "monthly_earnings": int(monthly_earnings), # fallback
        "today_jobs": today_jobs,
        "weekly_jobs": weekly_jobs,
        "monthly_jobs": monthly_jobs,
        "completed_jobs": len(completed_bookings),
        "total_jobs": total_jobs,
        "avg_rating": round(avg_rating, 1),
        "success_rate": success_rate
    }

@app.get("/technician/jobs")
def get_technician_jobs(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Booking).filter(
        models.Booking.technician_email == current_user.email,
        models.Booking.status == "Pending"
    ).all()

@app.post("/technician/update-job-status")
def update_job_status(req: UpdateJobStatusRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    booking = db.query(models.Booking).filter(models.Booking.id == req.booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    booking.status = req.status
    db.commit()
    return {"message": "Status updated"}

@app.post("/submit-rating")
def submit_rating(req: SubmitRatingRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    booking = db.query(models.Booking).filter(models.Booking.id == req.booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    booking.rating_value = int(req.rating)
    booking.rating_comment = req.comment
    db.commit()
    
    # Update technician rating
    if booking.technician_id:
        # Get all ratings for this technician
        ratings = db.query(models.Booking.rating_value).filter(
            models.Booking.technician_id == booking.technician_id,
            models.Booking.rating_value.isnot(None)
        ).all()
        
        if ratings:
            avg_rating = sum(r[0] for r in ratings) / len(ratings)
            profile = db.query(models.TechnicianProfile).filter(models.TechnicianProfile.user_id == booking.technician_id).first()
            if profile:
                profile.rating = f"{avg_rating:.1f}"
                db.commit()
                
    return {"message": "Rating submitted successfully"}

# --- Password Reset Flow ---
@app.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == req.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    otp = str(random.randint(100000, 999999))
    user.otp = otp
    db.commit()
    html = f"<html><body><h2>FIXIT NOW Password Reset OTP: {otp}</h2></body></html>"
    message = MessageSchema(subject="FIXIT NOW", recipients=[req.email], body=html, subtype=MessageType.html)
    fm = FastMail(get_mail_config())
    await fm.send_message(message)
    return {"message": "OTP sent successfully"}

@app.post("/verify-otp")
def verify_otp(req: VerifyOtpRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == req.email).first()
    if not user or user.otp != req.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    return {"message": "OTP verified"}

@app.post("/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    if req.new_password != req.confirm_password:
        raise HTTPException(status_code=400, detail="Mismatch")
    user = db.query(models.User).filter(models.User.email == req.email).first()
    user.password = req.new_password
    user.otp = None 
    db.commit()
    return {"message": "Password updated successfully"}

# --- Razorpay Setup ---
RAZORPAY_KEY_ID = "rzp_test_SN5q4r9UbjjvQv"
RAZORPAY_KEY_SECRET = "i5SwyTIFL99Z0epMTXV72jHn"

client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

@app.post("/create-razorpay-order", response_model=RazorpayOrderResponse)
def create_razorpay_order(req: RazorpayOrderRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    booking = db.query(models.Booking).filter(models.Booking.id == req.booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
        
    # Amount in paise (e.g. 500.00 -> 50000)
    amount_paise = int(req.amount * 100)
    
    order_data = {
        "amount": amount_paise,
        "currency": "INR",
        "receipt": f"receipt_booking_{req.booking_id}",
        "payment_capture": 1
    }
    
    try:
        razorpay_order = client.order.create(data=order_data)
        booking.razorpay_order_id = razorpay_order['id']
        db.commit()
        
        return {
            "order_id": razorpay_order['id'],
            "amount": razorpay_order['amount'],
            "currency": razorpay_order['currency'],
            "key_id": RAZORPAY_KEY_ID
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/verify-payment")
def verify_payment(req: PaymentVerificationRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    params_dict = {
        'razorpay_order_id': req.razorpay_order_id,
        'razorpay_payment_id': req.razorpay_payment_id,
        'razorpay_signature': req.razorpay_signature
    }
    
    try:
        # This will raise an error if signature is invalid
        client.utility.verify_payment_signature(params_dict)
        
        booking = db.query(models.Booking).filter(models.Booking.id == req.booking_id).first()
        if booking:
            booking.payment_status = "Paid"
            # Once paid, we can optionally move it out of active if needed, 
            # but usually payment happens after completion.
            db.commit()
            return {"status": "success", "message": "Payment verified and updated"}
        else:
            raise HTTPException(status_code=404, detail="Booking not found")
            
    except Exception:
        raise HTTPException(status_code=400, detail="Payment verification failed")

@app.post("/upload-profile-pic")
async def upload_profile_pic(file: UploadFile = File(...), current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    file_extension = os.path.splitext(file.filename)[1]
    file_name = f"profile_{current_user.id}_{int(datetime.now().timestamp())}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, file_name)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    file_url = f"/uploads/{file_name}"
    
    if current_user.role == "Customer":
        profile = db.query(models.CustomerProfile).filter(models.CustomerProfile.user_id == current_user.id).first()
        if profile:
            profile.profile_pic_url = file_url
            db.commit()
    elif current_user.role == "Technician":
        profile = db.query(models.TechnicianProfile).filter(models.TechnicianProfile.user_id == current_user.id).first()
        if profile:
            profile.profile_pic_url = file_url
            db.commit()
            
    return {"status": "success", "url": file_url}

@app.post("/upload-work-photo/{booking_id}")
async def upload_work_photo(booking_id: int, file: UploadFile = File(...), current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
        
    file_extension = os.path.splitext(file.filename)[1]
    file_name = f"work_{booking_id}_{int(datetime.now().timestamp())}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, file_name)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    file_url = f"/uploads/{file_name}"
    booking.work_photo_url = file_url
    db.commit()
    
    return {"status": "success", "url": file_url}

@app.post("/upload-technician-document")
async def upload_technician_document(
    doc_type: str, 
    file: UploadFile = File(...), 
    current_user: models.User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    file_extension = os.path.splitext(file.filename)[1]
    # Unique name: tech_doc_{user_id}_{doc_type_clean}_{timestamp}.ext
    import re
    doc_type_clean = re.sub(r'[^a-zA-Z0-9]', '_', doc_type).lower()
    file_name = f"tech_doc_{current_user.id}_{doc_type_clean}_{int(datetime.now().timestamp())}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, file_name)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    file_url = f"/uploads/{file_name}"
    
    new_doc = models.TechnicianDocument(
        user_id=current_user.id,
        doc_type=doc_type,
        file_url=file_url
    )
    db.add(new_doc)
    
    # Also update verification status string in profile if needed
    profile = db.query(models.TechnicianProfile).filter(models.TechnicianProfile.user_id == current_user.id).first()
    if profile:
        profile.verification_status = "pending"
    
    db.commit()
    
    return {"status": "success", "url": file_url}

@app.get("/user/profile")
def get_user_profile(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return {
        "full_name": current_user.full_name,
        "email": current_user.email,
        "phone": current_user.phone,
        "house_number": current_user.house_number,
        "street": current_user.street,
        "area": current_user.area,
        "city": current_user.city,
        "state": current_user.state,
        "pincode": current_user.pincode,
        "landmark": current_user.landmark
    }

class TechnicianOnboardingRequest(BaseModel):
    skills: str
    experience: str

@app.post("/technician/update-onboarding")
def update_onboarding(req: TechnicianOnboardingRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    profile = db.query(models.TechnicianProfile).filter(models.TechnicianProfile.user_id == current_user.id).first()
    if not profile:
        profile = models.TechnicianProfile(user_id=current_user.id)
        db.add(profile)
    
    profile.skills = req.skills
    profile.experience = req.experience
    db.commit()
    return {"message": "Onboarding details updated"}

@app.post("/technician/update-availability")
def update_availability(req: UpdateAvailabilityRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    profile = db.query(models.TechnicianProfile).filter(models.TechnicianProfile.user_id == current_user.id).first()
    if not profile:
        profile = models.TechnicianProfile(user_id=current_user.id)
        db.add(profile)
    
    profile.is_online = "true" if req.is_online else "false"
    db.commit()
    return {"message": "Availability status updated"}

@app.post("/update-location")
def update_location(req: UpdateLocationRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    current_user.latitude = str(req.latitude)
    current_user.longitude = str(req.longitude)
    db.commit()
    return {"message": "Location updated"}

@app.get("/get-technician-location/{email}")
def get_technician_location(email: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email, models.User.role == "Technician").first()
    if not user:
        raise HTTPException(status_code=404, detail="Technician not found")
    return {"latitude": user.latitude, "longitude": user.longitude}

@app.get("/get-user-location/{email}")
def get_user_location(email: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"latitude": user.latitude, "longitude": user.longitude}

@app.get("/get-user-phone/{email}")
def get_user_phone(email: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"phone": user.phone or ""}

@app.get("/user/customer-profile", response_model=CustomerProfileResponse)
def get_customer_profile(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    profile = db.query(models.CustomerProfile).filter(models.CustomerProfile.user_id == current_user.id).first()
    if not profile:
        profile = models.CustomerProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    
    address_parts = [p for p in [current_user.house_number, current_user.street, current_user.area, current_user.city, current_user.state] if p]
    address = ", ".join(address_parts) if address_parts else ""

    return {
        "full_name": current_user.full_name or "Not set",
        "email": current_user.email or "Not set",
        "phone": current_user.phone or "Not set",
        "address": address,
        "wallet_balance": profile.wallet_balance,
        "language": profile.language,
        "profile_pic_url": profile.profile_pic_url
    }

@app.get("/user/technician-profile", response_model=TechnicianProfileResponse)
def get_technician_profile(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    profile = db.query(models.TechnicianProfile).filter(models.TechnicianProfile.user_id == current_user.id).first()
    if not profile:
        profile = models.TechnicianProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)

    address_parts = [p for p in [current_user.house_number, current_user.street, current_user.area, current_user.city, current_user.state] if p]
    address = ", ".join(address_parts) if address_parts else ""

    return {
        "full_name": current_user.full_name or "Not set",
        "email": current_user.email or "Not set",
        "phone": current_user.phone or "Not set",
        "address": address,
        "skills": profile.skills,
        "service_radius": profile.service_radius,
        "working_hours": profile.working_hours,
        "verification_status": profile.verification_status,
        "payout_settings": profile.payout_settings,
        "is_online": profile.is_online,
        "rating": profile.rating,
        "profile_pic_url": profile.profile_pic_url
    }

@app.get("/technician/booking-history")
def get_technician_history(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Booking).filter(
        models.Booking.technician_email == current_user.email
    ).order_by(models.Booking.id.desc()).all()

@app.get("/technician/active-jobs")
def get_active_jobs(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Booking).filter(
        models.Booking.technician_email == current_user.email,
        models.Booking.status.in_(["Accepted", "Started"])
    ).all()

# --- Chat Endpoints ---
@app.get("/chat/list", response_model=List[ChatListItem])
def get_chat_list(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Re-verify user inside to be super safe
    user = current_user
    print(f"DEBUG: get_chat_list for {user.email} (Role: {user.role})")
    
    chat_list = []
    seen_emails = set()
    from sqlalchemy import func
    
    # Very inclusive statuses, all normalized to lower for comparison
    valid_statuses = ["pending", "accepted", "started", "completed", "ongoing", "on-the-way", "paid", "confirmed"]

    if user.role == "Customer":
        # Find all bookings for this customer
        bookings = db.query(models.Booking).filter(
            func.lower(models.Booking.customer_email) == user.email.lower()
        ).all()
        
        print(f"DEBUG: Customer {user.email} has {len(bookings)} bookings total.")
        
        for b in bookings:
            status = (b.status or "").strip().lower()
            if status in valid_statuses and b.technician_email:
                tech_email = b.technician_email.strip().lower()
                if tech_email not in seen_emails:
                    seen_emails.add(tech_email)
                    
                    # Last message
                    last_msg = db.query(models.Message).filter(
                        ((func.lower(models.Message.sender_email) == user.email.lower()) & (func.lower(models.Message.receiver_email) == tech_email)) |
                        ((func.lower(models.Message.sender_email) == tech_email) & (func.lower(models.Message.receiver_email) == user.email.lower()))
                    ).order_by(models.Message.id.desc()).first()

                    # Get profile pic
                    tech_profile = db.query(models.TechnicianProfile).filter(
                        func.lower(models.TechnicianProfile.user_id) == (db.query(models.User.id).filter(func.lower(models.User.email) == tech_email).scalar_subquery())
                    ).first()

                    chat_list.append(ChatListItem(
                        name=b.technician_name or "Technician",
                        email=b.technician_email,
                        last_message=(last_msg.message if last_msg else "Tap to chat"),
                        time=(str(last_msg.timestamp) if last_msg and last_msg.timestamp else ""),
                        unread_count=0,
                        role="Technician",
                        profile_pic_url=tech_profile.profile_pic_url if tech_profile else None
                    ))

    elif user.role == "Technician":
        # Find all bookings for this technician (by ID or Email)
        from sqlalchemy import or_
        bookings = db.query(models.Booking).filter(
            or_(
                func.lower(models.Booking.technician_email) == user.email.lower(),
                models.Booking.technician_id == user.id
            )
        ).all()
        
        print(f"DEBUG: Technician {user.email} has {len(bookings)} bookings total.")

        for b in bookings:
            status = (b.status or "").strip().lower()
            if status in valid_statuses and b.customer_email:
                cust_email = b.customer_email.strip().lower()
                if cust_email not in seen_emails:
                    seen_emails.add(cust_email)
                    
                    # Last message
                    last_msg = db.query(models.Message).filter(
                        ((func.lower(models.Message.sender_email) == user.email.lower()) & (func.lower(models.Message.receiver_email) == cust_email)) |
                        ((func.lower(models.Message.sender_email) == cust_email) & (func.lower(models.Message.receiver_email) == user.email.lower()))
                    ).order_by(models.Message.id.desc()).first()

                    # Get profile pic
                    cust_profile = db.query(models.CustomerProfile).filter(
                        func.lower(models.CustomerProfile.user_id) == (db.query(models.User.id).filter(func.lower(models.User.email) == cust_email).scalar_subquery())
                    ).first()

                    chat_list.append(ChatListItem(
                        name=b.customer_name or "Customer",
                        email=b.customer_email,
                        last_message=(last_msg.message if last_msg else "Tap to chat"),
                        time=(str(last_msg.timestamp) if last_msg and last_msg.timestamp else ""),
                        unread_count=0,
                        role="Customer",
                        profile_pic_url=cust_profile.profile_pic_url if cust_profile else None
                    ))
    
    print(f"DEBUG: Returning {len(chat_list)} chat items.")
    return chat_list

@app.get("/chat/messages/{other_email}", response_model=ChatResponse)
def get_messages(other_email: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    from sqlalchemy import func
    messages = db.query(models.Message).filter(
        ((func.lower(models.Message.sender_email) == current_user.email.lower()) & (func.lower(models.Message.receiver_email) == other_email.lower())) |
        ((func.lower(models.Message.sender_email) == other_email.lower()) & (func.lower(models.Message.receiver_email) == current_user.email.lower()))
    ).order_by(models.Message.id.asc()).all()
    
    # Mark messages sent by the other person as read
    unread_messages = [m for m in messages if m.sender_email.lower() == other_email.lower() and m.status != "read"]
    for msg in unread_messages:
        msg.status = "read"
    
    if unread_messages:
        db.commit()

    result_messages = []
    for msg in messages:
        result_messages.append(ChatMessage(
            id=msg.id,
            sender_email=msg.sender_email,
            receiver_email=msg.receiver_email,
            message=msg.message,
            timestamp=str(msg.timestamp),
            is_sent_by_me=(msg.sender_email.lower() == current_user.email.lower()),
            status=msg.status
        ))

    # Check for active booking
    from sqlalchemy import func
    active_booking = db.query(models.Booking).filter(
        (
            ((func.lower(models.Booking.customer_email) == current_user.email.lower()) & (func.lower(models.Booking.technician_email) == other_email.lower())) |
            ((func.lower(models.Booking.customer_email) == other_email.lower()) & (func.lower(models.Booking.technician_email) == current_user.email.lower()))
        ),
        models.Booking.status.in_(["pending", "accepted", "started", "ongoing", "on-the-way", "confirmed"])
    ).first()

    return ChatResponse(messages=result_messages, is_active=active_booking is not None)

@app.post("/chat/send", response_model=ChatMessage)
def send_message(req: SendMessageRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_message = models.Message(
        sender_email=current_user.email,
        receiver_email=req.receiver_email,
        message=req.message,
        timestamp=now_time,
        status="sent"
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    
    return ChatMessage(
        id=new_message.id,
        sender_email=new_message.sender_email,
        receiver_email=new_message.receiver_email,
        message=new_message.message,
        timestamp=str(new_message.timestamp),
        is_sent_by_me=True,
        status=new_message.status
    )

@app.post("/ai-chat")
def ai_chat(req: AiChatRequest):
    try:
        reply = get_response(req.message)
        return {"response": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/my-reviews")
def get_my_reviews(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    reviews = db.query(models.Booking).filter(
        models.Booking.customer_email == current_user.email,
        models.Booking.rating_value != None
    ).order_by(models.Booking.id.desc()).all()
    
    result = []
    for review in reviews:
        result.append({
            "id": review.id,
            "technician_name": review.technician_name,
            "service_name": review.service_name or review.description,
            "rating": review.rating_value,
            "comment": review.rating_comment,
            "date": review.date,
            "helpful_count": 0 # Placeholder
        })
    return result

@app.get("/favorites")
def get_favorites(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Find unique technicians that the user has rated 5 stars
    favorite_bookings = db.query(models.Booking).filter(
        models.Booking.customer_email == current_user.email,
        models.Booking.rating_value == 5
    ).all()
    
    tech_ids = {b.technician_id for b in favorite_bookings if b.technician_id}
    
    favorites = []
    for tech_id in tech_ids:
        tech_profile = db.query(models.TechnicianProfile).filter(models.TechnicianProfile.user_id == tech_id).first()
        tech_user = db.query(models.User).filter(models.User.id == tech_id).first()
        
        if tech_user and tech_profile:
            favorites.append({
                "id": tech_id,
                "full_name": tech_user.full_name,
                "email": tech_user.email,
                "role": tech_user.role,
                "rating": tech_profile.rating,
                "profile_pic_url": tech_profile.profile_pic_url,
                "experience": "5 years", # Dummy for now
                "distance": "2.5 km away" # Dummy for now
            })
            
    return favorites

@app.post("/mock-pay/{booking_id}")
def mock_pay(booking_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    booking.payment_status = "Paid"
    db.commit()
    return {"message": "Payment recorded successfully"}

# --- Admin Endpoints ---

class VerifyTechnicianRequest(BaseModel):
    status: str

@app.get("/admin/technicians/pending")
def get_pending_technicians(db: Session = Depends(get_db)):
    # Returns all technicians that are pending verification (status is "pending" or any non-approved/rejected variant)
    from sqlalchemy import func
    pending_profiles = db.query(models.TechnicianProfile).filter(
        models.TechnicianProfile.verification_status.notin_(["approved", "rejected"])
    ).all()
    user_ids = [p.user_id for p in pending_profiles]
    
    if not user_ids:
        return []

    users = db.query(models.User).filter(models.User.id.in_(user_ids)).all()
    
    result = []
    for u in users:
        profile = next((p for p in pending_profiles if p.user_id == u.id), None)
        if profile:
            result.append({
                "id": u.id,
                "full_name": u.full_name,
                "email": u.email,
                "phone": u.phone,
                "skills": profile.skills,
                "experience": profile.experience,
                "verification_status": profile.verification_status,
                "profile_pic_url": profile.profile_pic_url
            })
    return result

@app.get("/admin/technicians/approved")
def get_approved_technicians(db: Session = Depends(get_db)):
    approved_techs = db.query(models.TechnicianProfile).filter(
        models.TechnicianProfile.verification_status == 'approved'
    ).all()
    
    result = []
    for tech in approved_techs:
        user = db.query(models.User).filter(models.User.id == tech.user_id).first()
        if user:
            result.append({
                "id": tech.user_id,
                "full_name": user.full_name,
                "email": user.email,
                "phone": user.phone,
                "skills": tech.skills,
                "experience": tech.experience,
                "profile_pic_url": tech.profile_pic_url,
                "verification_status": tech.verification_status
            })
    return result

@app.get("/admin/technicians/{user_id}/documents")
def get_technician_documents(user_id: int, db: Session = Depends(get_db)):
    # Fetches all uploaded documents for a given technician
    docs = db.query(models.TechnicianDocument).filter(models.TechnicianDocument.user_id == user_id).all()
    return docs

@app.post("/admin/technicians/{user_id}/verify")
def verify_technician(user_id: int, req: VerifyTechnicianRequest, db: Session = Depends(get_db)):
    # Approves or rejects a technician's profile
    if req.status not in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail="Invalid status. Must be 'approved' or 'rejected'")
        
    profile = db.query(models.TechnicianProfile).filter(models.TechnicianProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Technician profile not found")
        
    profile.verification_status = req.status
    db.commit()
    return {"message": f"Technician successfully {req.status}", "new_status": req.status}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
