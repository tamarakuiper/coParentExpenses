import streamlit as st
from utils.auth import login_user, logout_user, is_logged_in, get_current_user

st.set_page_config(page_title="Log In", page_icon="🔐", layout="wide")

st.title("🔐 Log In")
st.write("Log in to your shared expense account.")

if is_logged_in():
    user = get_current_user()
    st.success(f"You are currently logged in as {user['user_name']}.")
    st.info(f"Household: {user['household_name']}")

    if st.button("Go to Home", type="primary"):
        st.rerun()

    if st.button("Log Out"):
        logout_user()
        st.success("You have been logged out.")
        st.rerun()

    st.stop()

with st.form("log_in_form"):
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Log In", type="primary")

if submitted:
    if not email.strip():
        st.error("Email is required.")
    elif not password:
        st.error("Password is required.")
    else:
        success, error_message = login_user(email.strip(), password)

        if success:
            st.rerun()
        else:
            st.error(error_message)