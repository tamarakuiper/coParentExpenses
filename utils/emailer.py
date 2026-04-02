import os
from resend import Resend

def send_household_invite_email(to_email: str, household_name: str, inviter_name: str, token: str):
    api_key = os.getenv("RESEND_API_KEY")
    base_url = os.getenv("APP_BASE_URL", "").rstrip("/")

    if not api_key:
        raise ValueError("RESEND_API_KEY is not set")

    if not base_url:
        raise ValueError("APP_BASE_URL is not set")

    resend = Resend(api_key=api_key)

    invite_link = f"{base_url}/Sign_Up?invite={token}"

    subject = f"{inviter_name} invited you to join {household_name} on Co-Parent Expenses"

    html = f"""
    <div style="font-family: Arial, sans-serif; line-height: 1.5;">
        <h2>You’ve been invited</h2>
        <p><strong>{inviter_name}</strong> invited you to join the household
        <strong>{household_name}</strong> in Co-Parent Expenses.</p>

        <p>
            <a href="{invite_link}"
               style="display:inline-block;padding:10px 16px;background:#2563eb;color:#fff;text-decoration:none;border-radius:6px;">
               Accept Invite
            </a>
        </p>

        <p>Or copy and paste this link into your browser:</p>
        <p>{invite_link}</p>
    </div>
    """

    response = resend.emails.send({
        "from": "Co-Parent Expenses <onboarding@resend.dev>",
        "to": [to_email],
        "subject": subject,
        "html": html,
    })

    return response