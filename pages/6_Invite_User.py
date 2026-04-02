import streamlit as st

from utils.auth import require_login
from utils.db import get_connection
from utils.invites import create_household_invite
from utils.emailer import send_household_invite_email

st.set_page_config(page_title="Invite User", page_icon="✉️", layout="wide")

current_user = require_login()


def get_current_user_email(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT email
        FROM users
        WHERE id = ?
        """,
        (user_id,),
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    try:
        return row["email"]
    except Exception:
        return row[0]


current_user_email = get_current_user_email(current_user["user_id"])

st.title("✉️ Invite User")
st.write("Invite another user to join your household.")

st.caption(
    f"Signed in as {current_user['user_name']} • Household: "
    f"{current_user.get('household_name', 'Unknown Household')}"
)

with st.form("invite_user_form"):
    invited_email = st.text_input("Invitee Email", placeholder="name@example.com")
    submitted = st.form_submit_button("Send Invite", type="primary")

if submitted:
    normalized_invited_email = invited_email.strip().lower()
    normalized_current_email = (current_user_email or "").strip().lower()

    if not normalized_invited_email:
        st.error("Email is required.")
    elif normalized_current_email and normalized_invited_email == normalized_current_email:
        st.error("You cannot invite yourself.")
    else:
        try:
            token = create_household_invite(
                invited_email=normalized_invited_email,
                invited_by_user_id=current_user["user_id"],
            )

            household_name = current_user.get("household_name", "your household")
            inviter_name = current_user.get("user_name", "A user")

            email_result = send_household_invite_email(
                to_email=normalized_invited_email,
                inviter_name=inviter_name,
                household_name=household_name,
                token=token,
            )

            st.success(f"Invite sent to {normalized_invited_email}")

        except ValueError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"Something went wrong while creating or sending the invite: {exc}")