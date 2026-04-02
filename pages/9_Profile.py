import streamlit as st

from utils.auth import require_login
from utils.db import get_connection

st.set_page_config(page_title="Profile", page_icon="👤", layout="wide")

current_user = require_login()


def fetch_user_profile(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            full_name,
            email,
            venmo_handle,
            zelle_email,
            zelle_phone
        FROM users
        WHERE id = ?
        LIMIT 1
        """,
        (user_id,),
    )

    row = cursor.fetchone()
    conn.close()
    return row


def update_user_profile(user_id, venmo_handle, zelle_email, zelle_phone):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE users
        SET
            venmo_handle = ?,
            zelle_email = ?,
            zelle_phone = ?
        WHERE id = ?
        """,
        (
            venmo_handle,
            zelle_email,
            zelle_phone,
            user_id,
        ),
    )

    conn.commit()
    conn.close()


profile = fetch_user_profile(current_user["user_id"])

if not profile:
    st.error("Could not load your profile.")
    st.stop()

st.title("👤 My Profile")
st.write("Manage the payment details other household members can use to reimburse you.")

st.info(
    f"Name: {profile['full_name']}  \n"
    f"Email: {profile['email']}  \n"
    f"Household: {current_user['household_name']}"
)

with st.form("profile_form"):
    venmo_handle = st.text_input(
        "Venmo Handle",
        value=profile["venmo_handle"] or "",
        placeholder="@yourhandle",
    )

    zelle_email = st.text_input(
        "Zelle Email",
        value=profile["zelle_email"] or "",
        placeholder="name@example.com",
    )

    zelle_phone = st.text_input(
        "Zelle Phone",
        value=profile["zelle_phone"] or "",
        placeholder="555-555-5555",
    )

    submitted = st.form_submit_button("Save Profile", type="primary")

if submitted:
    update_user_profile(
        user_id=current_user["user_id"],
        venmo_handle=venmo_handle.strip(),
        zelle_email=zelle_email.strip().lower(),
        zelle_phone=zelle_phone.strip(),
    )

    st.success("Profile updated successfully.")
    st.rerun()