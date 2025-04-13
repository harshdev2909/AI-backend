from fastapi import APIRouter, HTTPException
from models import UserProfile
from pydantic import BaseModel
from database import db
from bson import ObjectId
from utils.email_service import generate_otp, send_otp_email

router = APIRouter()
users_collection = db["users"]

def send_registration_email(email, user_id, otp):
    """
    Sends an email containing the user ID and OTP for verification.
    """
    body = f"""
    Dear User,

    Thank you for registering with INTELLICA.

    Your registration details:
    - **User ID**: {user_id}
    - **Verification OTP**: {otp}

    Please enter this OTP in the application to complete your registration.

    Best Regards,  
    **INTELLICA Team**
    """

    send_otp_email(email, body)

@router.post("/register/")
def register_user(user: UserProfile):
    otp = generate_otp()
    user_dict = user.dict()
    user_dict["otp"] = otp
    result = users_collection.insert_one(user_dict)
    user_id = str(result.inserted_id)

    # ✅ Send email with User ID & OTP
    send_registration_email(user.email, user_id, otp)

    return {
        "message": "OTP sent to email. Verify to complete registration.",
        "user_id": user_id
    }
class OTPRequest(BaseModel):
    user_id: str
    otp: str

@router.post("/verify_otp/")
def verify_otp(request: OTPRequest):
    user = users_collection.find_one({"_id": ObjectId(request.user_id)})
    if not user or user.get("otp") != request.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    users_collection.update_one({"_id": ObjectId(request.user_id)}, {"$unset": {"otp": ""}})
    return {"message": "Registration successful!"}