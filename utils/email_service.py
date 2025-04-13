import smtplib
import random
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from config import SMTP_SERVER, SMTP_PORT, SMTP_EMAIL, SMTP_PASSWORD

# Configure Logging
logging.basicConfig(level=logging.INFO)

def generate_otp():
    """Generate a secure 6-digit OTP."""
    return str(random.randint(100000, 999999))

def send_email(to_email, subject, html_content, retries=3, attachment_path=None):
    """
    Sends an email with retry logic and optional attachment.
    """
    msg = MIMEMultipart()
    msg["From"] = SMTP_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_content, "html"))

    # Attach a file if provided
    if attachment_path:
        try:
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f"attachment; filename={attachment_path.split('/')[-1]}")
                msg.attach(part)
        except Exception as e:
            logging.error(f"❌ Failed to attach file: {e}")

    for attempt in range(retries):
        try:
            logging.info(f"📩 Sending email to {to_email} (Attempt {attempt + 1}/{retries})...")
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
            server.quit()
            logging.info("✅ Email sent successfully!")
            return True
        except Exception as e:
            logging.error(f"❌ Email failed: {e}")
            if attempt == retries - 1:
                return False

def send_otp_email(email, otp):
    """
    Sends an OTP email with a professional format.
    """
    subject = "🔐 Intellica - Your OTP for Registration"
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; padding: 20px; border: 1px solid #ddd; border-radius: 10px; background-color: #f9f9f9;">
        <h2 style="color: #007bff; text-align: center;">Welcome to Intellica! 🚀</h2>
        <p style="text-align: center;">Your One-Time Password (OTP) for verification is:</p>
        <h1 style="text-align: center; color: #28a745; font-size: 32px;">{otp}</h1>
        <p style="text-align: center;">This OTP is valid for <b>5 minutes</b>. Please do not share it with anyone.</p>
        <hr style="border: 0; height: 1px; background: #ddd;">
        <p style="color: gray; font-size: 12px; text-align: center;">If you did not request this, please ignore this email.</p>
    </div>
    """
    return send_email(email, subject, html_content)

def send_course_recommendation_email(email, courses):
    """
    Sends a beautifully formatted email with course recommendations.
    """
    subject = "🎓 Apurv.AI - Your AI-Powered Course Recommendations!"

    # Ensure all courses have valid links
    course_list = ""
    for c in courses:
        course_name = c.title  # Direct attribute access
        platform = c.platform
        link = c.link  # Fallback to "#" if no link is found
        price = getattr(c, "price", "N/A")
        difficulty = getattr(c, "difficulty_level", "Unknown Level")
        
        course_list += f"""
        <li style='margin-bottom: 15px; font-size: 16px;'>
            <b>{course_name}</b> - {platform} <br>
            <a href='{link}' style='color: #007bff; text-decoration: none;'>View Course</a><br>
            <span style="color: gray;">Price: ${price} | Level: {difficulty}</span>
        </li>
        """

    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; padding: 20px; border: 1px solid #ddd; border-radius: 10px; background-color: #f9f9f9;">
        <h2 style="color: #007bff; text-align: center;">Hi there! 👋</h2>
        <p style="text-align: center;">Based on your specialization , here are your top course recommendations:</p>
        <ul style="padding-left: 20px; list-style-type: none;">{course_list}</ul>
        <hr style="border: 0; height: 1px; background: #ddd;">
        <p style="text-align: center;">Happy Learning! 🚀</p>
        <p style="text-align: center;"><b>Best Regards,<br>Apurv Inc.</b></p>
    </div>
    """
    return send_email(email, subject, html_content)

