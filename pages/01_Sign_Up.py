import streamlit as st

from utils.auth import (
    create_user,
    create_user_with_household,
    login_user,
    is_logged_in,
    get_current_user,
)
from utils.invites import get_invite_by_token, accept_household_invite

st.set_page_config(page_title="Sign Up", page_icon="🆕", layout="wide")


def invite_get(invite, key, default=None):
    if invite is None:
        return default

    try:
        return invite[key]
    except Exception:
        pass

    # Fallback for tuple-style rows
    mapping = {
        "id": 0,
        "household_id": 1,
        "invited_email": 2,
        "invited_by_user_id": 3,
        "token": 4,
        "status": 5,
        "expires_at": 6,
        "created_at": 7,
        "accepted_by_user_id": 8,
        "household_name": 9,
        "inviter_name": 10,
    }

    idx = mapping.get(key)
    if idx is None:
        return default

    try:
        return invite[idx]
    except Exception:
        return default


st.title("🆕 Sign Up")
st.write("Create your account.")

if is_logged_in():
    user = get_current_user()
    st.success(f"You are already logged in as {user['user_name']}.")
    st.info(f"Household: {user['household_name']}")
    st.stop()

with st.form("sign_up_form"):
    full_name = st.text_input("Full Name")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    invite_code = st.text_input("Invite Code (optional)")

    invite = None
    normalized_code = invite_code.strip()
    if normalized_code:
        invite = get_invite_by_token(normalized_code)

    if invite:
        st.info(
            f"You are joining: {invite_get(invite, 'household_name')} "
            f"(invited by {invite_get(invite, 'inviter_name')})"
        )
        household_name = ""
    else:
        household_name = st.text_input(
            "Household Name",
            placeholder="Example: Tamara & Matt Household",
        )

    submitted = st.form_submit_button("Create Account", type="primary")

if submitted:
    normalized_email = email.strip().lower()
    normalized_code = invite_code.strip()

    if not full_name.strip():
        st.error("Full Name is required.")
    elif not normalized_email:
        st.error("Email is required.")
    elif not password:
        st.error("Password is required.")
    elif len(password) < 8:
        st.error("Password must be at least 8 characters long.")
    elif password != confirm_password:
        st.error("Passwords do not match.")
    elif normalized_code and not invite:
        st.error("Invite code is invalid.")
    elif invite and invite_get(invite, "invited_email", "").strip().lower() != normalized_email:
        st.error("This invite code was issued for a different email address.")
    elif not invite and not household_name.strip():
        st.error("Household Name is required when no invite code is used.")
    else:
        try:
            if invite:
                user_id = create_user(
                    full_name=full_name,
                    email=normalized_email,
                    password=password,
                )

                ok, message = accept_household_invite(
                    token=normalized_code,
                    current_user_id=user_id,
                    current_user_email=normalized_email,
                )

                if not ok:
                    st.error(message)
                    st.stop()
            else:
                create_user_with_household(
                    full_name=full_name,
                    email=normalized_email,
                    password=password,
                    household_name=household_name.strip(),
                )

            success, error_message = login_user(normalized_email, password)

            if success:
                st.success("Account created successfully.")
                st.info("Use the sidebar to continue.")
            else:
                st.warning("Account was created, but automatic login failed.")
                st.info(error_message)

        except ValueError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"Something went wrong while creating the account: {exc}")