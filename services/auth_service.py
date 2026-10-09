"""
services/auth_service.py

Handles email OTP authentication:

- Generates a 6-digit one-time-password, sends it via SendGrid
  (or plain SMTP fallback), and validates the code the learner types back.

Google OAuth is handled entirely by Streamlit's built-in st.login() /
st.user using credentials in .streamlit/secrets.toml — no manual token
verification needed here.

Environment variables consumed
-------------------------------
SENDGRID_API_KEY          — SendGrid API key (preferred sender)
EMAIL_FROM                — verified sender address, e.g. noreply@parrhet.ai
SMTP_HOST / SMTP_PORT /   — plain-SMTP fallback when SENDGRID_API_KEY is absent
SMTP_USER / SMTP_PASSWORD
OTP_EXPIRY_SECONDS        — how long a code is valid (default: 600 = 10 min)
"""

import os
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone, timedelta
from typing import Tuple

from dotenv import load_dotenv

from services.logger import rhet_log

load_dotenv()

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

OTP_LENGTH: int = 6
OTP_EXPIRY_SECONDS: int = int(os.getenv("OTP_EXPIRY_SECONDS", "600"))  # 10 minutes
EMAIL_FROM: str = os.getenv("EMAIL_FROM", "noreply@parrhet.ai")


# ---------------------------------------------------------------------------
# EMAIL OTP — GENERATION
# ---------------------------------------------------------------------------

def generate_otp() -> str:
    """Return a cryptographically random 6-digit numeric string."""
    return "".join(random.choices(string.digits, k=OTP_LENGTH))


def otp_expiry() -> datetime:
    """Return a timezone-aware UTC datetime OTP_EXPIRY_SECONDS from now."""
    return datetime.now(timezone.utc) + timedelta(seconds=OTP_EXPIRY_SECONDS)


# ---------------------------------------------------------------------------
# EMAIL OTP — SENDING
# ---------------------------------------------------------------------------

def send_otp_email(to_email: str, otp_code: str, user_name: str = "") -> Tuple[bool, str]:
    """
    Send a verification OTP email to *to_email*.

    Tries SendGrid first (when SENDGRID_API_KEY is set); falls back to plain
    SMTP using SMTP_HOST / SMTP_USER / SMTP_PASSWORD.

    Parameters
    ----------
    to_email  : recipient address
    otp_code  : the 6-digit code to embed in the email
    user_name : optional first name used for the greeting

    Returns
    -------
    (success, error_message) — error_message is empty string on success
    """
    subject = "Your parrhet.ai verification code"
    greeting = f"Hi {user_name}," if user_name else "Hi,"
    minutes = OTP_EXPIRY_SECONDS // 60

    html_body = f"""
    <div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;padding:32px 24px;
                background:#FDFAF5;border-radius:12px;border:1px solid #E0D9C8;">
      <h2 style="font-family:Georgia,serif;font-style:italic;color:#1A1710;margin-bottom:8px;">
        parrhet<span style="color:#C45030;">.ai</span>
      </h2>
      <p style="color:#1A1710;font-size:15px;margin-bottom:24px;">{greeting}</p>
      <p style="color:#3A3520;font-size:15px;line-height:1.6;margin-bottom:24px;">
        Use the code below to verify your identity. It expires in {minutes} minutes.
      </p>
      <div style="background:#F0EBE0;border:2px dashed #6B7A46;border-radius:10px;
                  padding:20px;text-align:center;margin-bottom:28px;">
        <span style="font-family:'Courier New',monospace;font-size:36px;font-weight:700;
                     letter-spacing:12px;color:#4A5920;">{otp_code}</span>
      </div>
      <p style="color:#7A7260;font-size:13px;line-height:1.6;">
        If you did not request this, you can safely ignore this email.
      </p>
      <hr style="border:none;border-top:1px solid #E0D9C8;margin:24px 0;">
      <p style="color:#9A9080;font-size:12px;">parrhet.ai — language learning powered by AI</p>
    </div>
    """

    text_body = (
        f"{greeting}\n\n"
        f"Your parrhet.ai verification code is: {otp_code}\n\n"
        f"It expires in {minutes} minutes.\n\n"
        "If you did not request this, ignore this email.\n\n"
        "— parrhet.ai"
    )

    sendgrid_key = os.getenv("SENDGRID_API_KEY", "")

    if sendgrid_key:
        return _send_via_sendgrid(
            sendgrid_key,
            to_email,
            subject,
            html_body,
            text_body
        )

    # Fallback: plain SMTP
    return _send_via_smtp(to_email, subject, html_body, text_body)


def _send_via_sendgrid(
    api_key: str,
    to_email: str,
    subject: str,
    html_body: str,
    text_body: str
) -> Tuple[bool, str]:
    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail, Email, To, Content

        sg = sendgrid.SendGridAPIClient(api_key=api_key)
        message = Mail(
            from_email=Email(EMAIL_FROM),
            to_emails=To(to_email),
            subject=subject,
            html_content=Content("text/html", html_body),
        )
        response = sg.send(message)

        if response.status_code in (200, 201, 202):
            return True, ""

        return False, f"SendGrid returned status {response.status_code}"

    except ImportError:
        rhet_log.warning("sendgrid package not installed; falling back to SMTP.")
        return _send_via_smtp(to_email, subject, html_body, text_body)

    except Exception as exc:
        rhet_log.error("_send_via_sendgrid failed: %s", exc, exc_info=True)
        return False, f"SendGrid error: {exc}"


def _send_via_smtp(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: str
) -> Tuple[bool, str]:
    host = os.getenv("SMTP_HOST", "")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "")
    password = os.getenv("SMTP_PASSWORD", "")

    if not host or not user or not password:
        return False, (
            "No email provider is configured. "
            "Set SENDGRID_API_KEY or SMTP_HOST / SMTP_USER / SMTP_PASSWORD in .env."
        )

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = EMAIL_FROM
        msg["To"] = to_email
        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(host, port) as server:
            server.ehlo()
            server.starttls()
            server.login(user, password)
            server.sendmail(EMAIL_FROM, [to_email], msg.as_string())

        return True, ""

    except Exception as exc:
        rhet_log.error("_send_via_smtp failed: %s", exc, exc_info=True)
        return False, f"SMTP error: {exc}"


# ---------------------------------------------------------------------------
# EMAIL OTP — VERIFICATION
# ---------------------------------------------------------------------------

def verify_otp(
    entered_code: str,
    stored_code: str,
    expires_at_iso: str,
) -> Tuple[bool, str]:
    """
    Validate a user-entered OTP against the stored code and expiry.

    Parameters
    ----------
    entered_code   : the code the user typed into the form
    stored_code    : the OTP that was generated and emailed
    expires_at_iso : ISO-8601 UTC timestamp when the code expires

    Returns
    -------
    (valid, reason) — reason is an empty string on success, human-readable
                      message on failure suitable for displaying in the UI
    """
    if not entered_code or not stored_code:
        return False, "Missing verification code."

    try:
        expires_at = datetime.fromisoformat(expires_at_iso)
        # Make timezone-aware if naive
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return False, "Invalid expiry timestamp."

    if datetime.now(timezone.utc) > expires_at:
        return False, "Verification code has expired. Please request a new one."

    if entered_code.strip() != stored_code.strip():
        return False, "Incorrect verification code."

    return True, ""
