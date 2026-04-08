"""
Email Service - Sends OTP verification emails via SMTP
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env first, then .env.example as fallback
backend_dir = Path(__file__).resolve().parent.parent.parent
load_dotenv(backend_dir / ".env")
load_dotenv(backend_dir / ".env.example")  # fallback if .env doesn't exist


# ──── Configuration ───────────────────────────────────────────────
# Gmail SMTP settings
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")    # App password for Gmail
SMTP_SENDER_NAME = os.getenv("SMTP_SENDER_NAME", "ClaimAssist AI")


def send_otp_email(to_email: str, otp_code: str, user_name: str = "User") -> bool:
    """
    Send OTP verification email.
    Returns True if sent successfully, False otherwise.
    """
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        print("[EMAIL] SMTP not configured — skipping email send")
        print(f"[EMAIL] OTP for {to_email}: {otp_code}")
        return False

    try:
        # Create the email
        msg = MIMEMultipart("alternative")
        msg["From"] = f"{SMTP_SENDER_NAME} <{SMTP_EMAIL}>"
        msg["To"] = to_email
        msg["Subject"] = f"Your ClaimAssist Verification Code: {otp_code}"

        # HTML email body
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin:0;padding:0;background-color:#f4f5f7;font-family:'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f5f7;padding:40px 20px;">
                <tr>
                    <td align="center">
                        <table width="480" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
                            
                            <!-- Header -->
                            <tr>
                                <td style="background:linear-gradient(135deg,#5A67D8 0%,#667EEA 100%);padding:32px 40px;text-align:center;">
                                    <h1 style="margin:0;color:#ffffff;font-size:24px;font-weight:800;letter-spacing:-0.5px;">
                                        🛡️ ClaimAssist AI
                                    </h1>
                                    <p style="margin:8px 0 0;color:rgba(255,255,255,0.8);font-size:14px;">
                                        AI-Powered Insurance Claim Appeals
                                    </p>
                                </td>
                            </tr>
                            
                            <!-- Body -->
                            <tr>
                                <td style="padding:40px;">
                                    <p style="margin:0 0 8px;color:#374151;font-size:16px;">
                                        Hello <strong>{user_name}</strong>,
                                    </p>
                                    <p style="margin:0 0 24px;color:#6B7280;font-size:14px;line-height:1.6;">
                                        You requested to verify your email address for your ClaimAssist account. 
                                        Use the verification code below to complete your registration.
                                    </p>
                                    
                                    <!-- OTP Box -->
                                    <table width="100%" cellpadding="0" cellspacing="0">
                                        <tr>
                                            <td align="center" style="padding:24px 0;">
                                                <div style="background:#F3F4FF;border:2px dashed #5A67D8;border-radius:12px;padding:20px 32px;display:inline-block;">
                                                    <p style="margin:0 0 4px;color:#6B7280;font-size:12px;text-transform:uppercase;letter-spacing:1px;font-weight:600;">
                                                        Verification Code
                                                    </p>
                                                    <p style="margin:0;color:#5A67D8;font-size:36px;font-weight:800;letter-spacing:8px;">
                                                        {otp_code}
                                                    </p>
                                                </div>
                                            </td>
                                        </tr>
                                    </table>
                                    
                                    <p style="margin:24px 0 0;color:#6B7280;font-size:13px;line-height:1.6;">
                                        ⏱️ This code expires in <strong>10 minutes</strong>. 
                                        If you didn't request this code, please ignore this email.
                                    </p>
                                </td>
                            </tr>
                            
                            <!-- Footer -->
                            <tr>
                                <td style="background:#F9FAFB;padding:20px 40px;text-align:center;border-top:1px solid #E5E7EB;">
                                    <p style="margin:0;color:#9CA3AF;font-size:12px;">
                                        © 2026 ClaimAssist AI · Automated Health Insurance Claim Appeals
                                    </p>
                                    <p style="margin:4px 0 0;color:#D1D5DB;font-size:11px;">
                                        This is an automated email. Please do not reply.
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

        # Plain text fallback
        plain_text = f"""
Hello {user_name},

Your ClaimAssist verification code is: {otp_code}

This code expires in 10 minutes. If you didn't request this, please ignore this email.

— ClaimAssist AI Team
        """

        msg.attach(MIMEText(plain_text, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        # Send via SMTP
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)

        print(f"[EMAIL] OTP sent successfully to {to_email}")
        return True

    except Exception as e:
        print(f"[EMAIL] Failed to send OTP to {to_email}: {e}")
        return False


def send_password_reset_email(to_email: str, reset_link: str, user_name: str = "User") -> bool:
    """
    Send password reset email with a reset link.
    Returns True if sent successfully, False otherwise.
    """
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        print("[EMAIL] SMTP not configured — skipping password reset email")
        print(f"[EMAIL] Reset link for {to_email}: {reset_link}")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"{SMTP_SENDER_NAME} <{SMTP_EMAIL}>"
        msg["To"] = to_email
        msg["Subject"] = "Reset Your ClaimAssist Password"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
        <body style="margin:0;padding:0;background-color:#f4f5f7;font-family:'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f5f7;padding:40px 20px;">
                <tr><td align="center">
                    <table width="480" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
                        <tr><td style="background:linear-gradient(135deg,#5A67D8 0%,#667EEA 100%);padding:32px 40px;text-align:center;">
                            <h1 style="margin:0;color:#ffffff;font-size:24px;font-weight:800;">🛡️ ClaimAssist AI</h1>
                            <p style="margin:8px 0 0;color:rgba(255,255,255,0.8);font-size:14px;">Password Reset Request</p>
                        </td></tr>
                        <tr><td style="padding:40px;">
                            <p style="margin:0 0 8px;color:#374151;font-size:16px;">Hello <strong>{user_name}</strong>,</p>
                            <p style="margin:0 0 24px;color:#6B7280;font-size:14px;line-height:1.6;">
                                We received a request to reset the password for your ClaimAssist account. 
                                Click the button below to set a new password.
                            </p>
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr><td align="center" style="padding:16px 0;">
                                    <a href="{reset_link}" style="display:inline-block;background:linear-gradient(135deg,#5A67D8,#667EEA);color:#ffffff;text-decoration:none;padding:14px 40px;border-radius:12px;font-size:16px;font-weight:700;letter-spacing:0.5px;">
                                        Reset Password
                                    </a>
                                </td></tr>
                            </table>
                            <p style="margin:24px 0 8px;color:#6B7280;font-size:13px;line-height:1.6;">
                                Or copy and paste this link in your browser:
                            </p>
                            <p style="margin:0;padding:12px;background:#F3F4FF;border-radius:8px;word-break:break-all;font-size:12px;color:#5A67D8;">
                                {reset_link}
                            </p>
                            <p style="margin:24px 0 0;color:#9CA3AF;font-size:12px;">
                                ⏱️ This link expires in <strong>30 minutes</strong>. If you didn't request this, please ignore this email.
                            </p>
                        </td></tr>
                        <tr><td style="background:#F9FAFB;padding:20px 40px;text-align:center;border-top:1px solid #E5E7EB;">
                            <p style="margin:0;color:#9CA3AF;font-size:12px;">© 2026 ClaimAssist AI</p>
                        </td></tr>
                    </table>
                </td></tr>
            </table>
        </body>
        </html>
        """

        plain_text = f"Hello {user_name},\n\nReset your password here: {reset_link}\n\nThis link expires in 30 minutes.\n\n— ClaimAssist AI Team"

        msg.attach(MIMEText(plain_text, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)

        print(f"[EMAIL] Password reset email sent to {to_email}")
        return True

    except Exception as e:
        print(f"[EMAIL] Failed to send reset email to {to_email}: {e}")
        return False
