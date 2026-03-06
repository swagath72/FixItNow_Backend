from fastapi import FastAPI, Depends, HTTPException, Header, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import razorpay
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from datetime import datetime
from typing import List, Optional
import random
import uvicorn
import os
import shutil

import models
from database import SessionLocal, engine

# Automatically create/update tables in MySQL
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Make sure uploads directory exists
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# --- Email Configuration (Replace with actual Gmail App Password) ---
conf = ConnectionConfig(
    MAIL_USERNAME="---------------",
    MAIL_PASSWORD="----------------", 
    MAIL_FROM="---------------------",
    MAIL_PORT=465,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_FROM_NAME="FIXIT NOW Support",
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=None
)

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

class ChatResponse(BaseModel):
    messages: List[ChatMessage]
    is_active: bool

# --- Auth Dependency ---
async def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Token")
    email = authorization.replace("Bearer ", "")
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")
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
        models.Booking.status != "Completed",
        models.Booking.status != "Cancelled"
    ).order_by(models.Booking.id.desc()).first()

    profile_pic_url = None
    if user.role == "Customer":
        profile = db.query(models.CustomerProfile).filter(models.CustomerProfile.user_id == user.id).first()
        if profile:
            profile_pic_url = profile.profile_pic_url
    elif user.role == "Technician":
        profile = db.query(models.TechnicianProfile).filter(models.TechnicianProfile.user_id == user.id).first()
        if profile:
            profile_pic_url = profile.profile_pic_url

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
        "profile_pic_url": profile_pic_url
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
def get_recent_bookings(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    today_date = datetime.now().strftime("%d/%m/%Y")
    return db.query(models.Booking).filter(
        models.Booking.customer_email == current_user.email,
        models.Booking.date == today_date
    ).order_by(models.Booking.id.desc()).all()

@app.get("/booking-history")
def get_history(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Booking).filter(
        models.Booking.customer_email == current_user.email
    ).order_by(models.Booking.id.desc()).all()

@app.get("/technicians")
def get_technicians(db: Session = Depends(get_db)):
    technicians = db.query(models.User).filter(models.User.role == "Technician").all()
    return [{"id": t.id, "full_name": t.full_name, "role": t.role, "experience": "5 years"} for t in technicians]

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

# --- Technician Endpoints ---
from datetime import datetime, timedelta
import re

@app.get("/technician/earnings")
def get_technician_earnings(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    completed_bookings = db.query(models.Booking).filter(
        models.Booking.technician_email == current_user.email,
        models.Booking.status == "Completed"
    ).all()

    today_earnings = 0
    week_earnings = 0
    month_earnings = 0

    now = datetime.now()
    today_str = now.strftime("%d/%m/%Y")
    current_month_str = now.strftime("%m/%Y")
    
    # Calculate 7 days ago at midnight for "This week"
    seven_days_ago = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=7)

    for booking in completed_bookings:
        # Extract numeric cost
        raw_cost = booking.cost or "0"
        # Remove non-numeric characters except maybe decimal points if they exist, but simple regex is fine:
        cost_str = re.sub(r'[^\d.]', '', raw_cost)
        try:
            cost = float(cost_str) if cost_str else 0.0
        except ValueError:
            cost = 0.0

        if not booking.date:
            continue
            
        # Check Today
        if booking.date == today_str:
            today_earnings += cost
            
        # Check Month (ends with mm/yyyy)
        if booking.date.endswith(current_month_str):
            month_earnings += cost
            
        # Check Week (parse date)
        try:
            booking_date = datetime.strptime(booking.date, "%d/%m/%Y")
            if seven_days_ago <= booking_date <= now:
                week_earnings += cost
        except ValueError:
            pass # Invalid date format

    return {
        "today_earnings": str(int(today_earnings)),
        "week_earnings": str(int(week_earnings)),
        "month_earnings": str(int(month_earnings))
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
    if booking:
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
    otp = str(random.randint(1000, 9999))
    user.otp = otp
    db.commit()
    html = f"<html><body><h2>FIXIT NOW Password Reset OTP: {otp}</h2></body></html>"
    message = MessageSchema(subject="FIXIT NOW", recipients=[req.email], body=html, subtype=MessageType.html)
    fm = FastMail(conf)
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
        profile.verification_status = "Pending Review"
    
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
    chat_list = []
    seen_emails = set()
    
    # We look for people this user has bookings with
    if current_user.role == "Customer":
        # Find technicians from accepted/started/completed bookings
        related_bookings = db.query(models.Booking).filter(
            models.Booking.customer_email == current_user.email,
            models.Booking.status.in_(["Accepted", "Started", "Completed"])
        ).all()
        
        for booking in related_bookings:
            if booking.technician_email not in seen_emails:
                seen_emails.add(booking.technician_email)
                
                # Get last message
                last_msg = db.query(models.Message).filter(
                    ((models.Message.sender_email == current_user.email) & (models.Message.receiver_email == booking.technician_email)) |
                    ((models.Message.sender_email == booking.technician_email) & (models.Message.receiver_email == current_user.email))
                ).order_by(models.Message.id.desc()).first()

                chat_list.append(ChatListItem(
                    name=booking.technician_name or "Technician",
                    email=booking.technician_email,
                    last_message=last_msg.message if last_msg else "Tap to chat",
                    time=str(last_msg.timestamp) if last_msg and last_msg.timestamp else "",
                    unread_count=0,
                    role="Technician"
                ))

    elif current_user.role == "Technician":
        # Find customers from accepted/started/completed bookings
        related_bookings = db.query(models.Booking).filter(
            models.Booking.technician_email == current_user.email,
            models.Booking.status.in_(["Accepted", "Started", "Completed"])
        ).all()

        for booking in related_bookings:
            if booking.customer_email not in seen_emails:
                seen_emails.add(booking.customer_email)
                
                # Get last message
                last_msg = db.query(models.Message).filter(
                    ((models.Message.sender_email == current_user.email) & (models.Message.receiver_email == booking.customer_email)) |
                    ((models.Message.sender_email == booking.customer_email) & (models.Message.receiver_email == current_user.email))
                ).order_by(models.Message.id.desc()).first()

                chat_list.append(ChatListItem(
                    name=booking.customer_name or "Customer",
                    email=booking.customer_email,
                    last_message=last_msg.message if last_msg else "Tap to chat",
                    time=str(last_msg.timestamp) if last_msg and last_msg.timestamp else "",
                    unread_count=0,
                    role="Customer"
                ))
    
    return chat_list

@app.get("/chat/messages/{other_email}", response_model=ChatResponse)
def get_messages(other_email: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    messages = db.query(models.Message).filter(
        ((models.Message.sender_email == current_user.email) & (models.Message.receiver_email == other_email)) |
        ((models.Message.sender_email == other_email) & (models.Message.receiver_email == current_user.email))
    ).order_by(models.Message.id.asc()).all()
    
    # Mark messages sent by the other person as read
    unread_messages = [m for m in messages if m.sender_email == other_email and m.status != "read"]
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
            is_sent_by_me=(msg.sender_email == current_user.email),
            status=msg.status
        ))

    # Check for active booking
    active_booking = db.query(models.Booking).filter(
        (
            ((models.Booking.customer_email == current_user.email) & (models.Booking.technician_email == other_email)) |
            ((models.Booking.customer_email == other_email) & (models.Booking.technician_email == current_user.email))
        ),
        models.Booking.status.in_(["Pending", "Accepted", "Started"])
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
