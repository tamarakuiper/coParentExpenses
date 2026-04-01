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

query_params = st.query_params
invite_from_url = query_params.get("invite", "")

if isinstance(invite_from_url, list):
    invite_from_url = invite_from_url[0] if invite_from_url else ""

invite_code = st.text_input(
    "Invite Code (optional)",
    value=invite_from_url,
)

normalized_code = invite_code.strip()
invite = get_invite_by_token(normalized_code) if normalized_code else None
invite_valid = invite is not None

prefilled_email = invite_get(invite, "invited_email", "") if invite_valid else ""

if normalized_code:
    if invite_valid:
        st.info(
            f"You are joining: {invite_get(invite, 'household_name')} "
            f"(invited by {invite_get(invite, 'inviter_name')})"
        )
    else:
        st.warning("Invite code not found or invalid.")

with st.form("sign_up_form"):
    full_name = st.text_input("Full Name")

    email = st.text_input(
        "Email",
        value=prefilled_email,
        disabled=invite_valid,
        placeholder="name@example.com",
    )

    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

    household_name = ""
    if not normalized_code:
        household_name = st.text_input(
            "Household Name",
            placeholder="Example: Tamara & Matt Household",
        )

    submitted = st.form_submit_button("Create Account", type="primary")

if submitted:
    normalized_email = (prefilled_email if invite_valid else email).strip().lower()

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
    elif normalized_code and not invite_valid:
        st.error("Invite code is invalid.")
    elif invite_valid and invite_get(invite, "invited_email", "").strip().lower() != normalized_email:
        st.error("This invite code was issued for a different email address.")
    elif not normalized_code and not household_name.strip():
        st.error("Household Name is required when no invite code is used.")
    else:
        try:
            if normalized_code:
                user_id = create_user(
                    full_name=full_name.strip(),
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
                    full_name=full_name.strip(),
                    email=normalized_email,
                    password=password,
                    household_name=household_name.strip(),
                )

            success, error_message = login_user(normalized_email, password)

            if success:
                st.switch_page("app/Home.py")
            else:
                st.warning("Account was created, but automatic login failed.")
                st.info(error_message)

        except ValueError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"Something went wrong while creating the account: {exc}")