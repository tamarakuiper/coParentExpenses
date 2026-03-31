import streamlit as st

from utils.auth import create_user_with_household, login_user, is_logged_in, get_current_user

st.set_page_config(page_title="Sign Up", page_icon="🆕", layout="wide")

st.title("🆕 Sign Up")
st.write("Create your account and your shared expense household.")

if is_logged_in():
    user = get_current_user()
    st.success(f"You are already logged in as {user['user_name']}.")
    st.info(f"Household: {user.get('household_name', 'Unknown Household')}")
    st.stop()

with st.form("sign_up_form"):
    full_name = st.text_input("Full Name")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    household_name = st.text_input(
        "Household Name",
        placeholder="Example: Tamara & Matt Household",
    )

    submitted = st.form_submit_button("Create Account", type="primary")

if submitted:
    if not full_name.strip():
        st.error("Full Name is required.")
    elif not email.strip():
        st.error("Email is required.")
    elif not password:
        st.error("Password is required.")
    elif len(password) < 8:
        st.error("Password must be at least 8 characters long.")
    elif password != confirm_password:
        st.error("Passwords do not match.")
    elif not household_name.strip():
        st.error("Household Name is required.")
    else:
        try:
            create_user_with_household(
                full_name=full_name.strip(),
                email=email.strip(),
                password=password,
                household_name=household_name.strip(),
            )

            success, error_message = login_user(email.strip(), password)

            if success:
                st.success("Account created successfully.")
                st.info("Use the sidebar to go to Home, Add Expense, or Ledger.")
            else:
                st.warning("Account was created, but automatic login failed.")
                st.info(error_message)

        except ValueError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"Something went wrong while creating the account: {exc}")
