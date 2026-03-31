import streamlit as st

from utils.auth import require_login
from utils.db import get_connection
from utils.invites import accept_household_invite, get_invite_by_token

st.set_page_config(page_title="Accept Invite", page_icon="✅", layout="wide")

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
    except (TypeError, KeyError, IndexError):
        return row[0]


current_user_email = get_current_user_email(current_user["user_id"])

st.title("✅ Accept Household Invite")
st.write("Join a household using an invite code.")

caption_email = current_user_email or "email not found"
st.caption(f"Signed in as {current_user['user_name']} ({caption_email})")

invite_code = st.text_input("Invite Code")

if invite_code:
    invite = get_invite_by_token(invite_code.strip())
    if invite:
        st.info(
            f"Household: {invite['household_name']} • Invited by: {invite['inviter_name']} • Sent to: {invite['invited_email']}"
        )
    else:
        st.warning("Invite code not found.")

if st.button("Accept Invite", type="primary"):
    if not invite_code.strip():
        st.error("Enter an invite code.")
    elif not current_user_email:
        st.error("Could not determine the signed-in user's email.")
    else:
        ok, message = accept_household_invite(
            token=invite_code.strip(),
            current_user_id=current_user["user_id"],
            current_user_email=current_user_email,
        )

        if ok:
            st.success(message)
            st.info("Log out and log back in if the household label does not refresh immediately.")
        else:
            st.error(message)