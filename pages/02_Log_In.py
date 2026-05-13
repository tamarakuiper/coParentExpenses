import streamlit as st
from utils.auth import login_user, logout_user, is_logged_in, get_current_user

st.set_page_config(page_title="Log In", page_icon="🔐", layout="wide")

st.markdown(
    """
    <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(37, 99, 235, 0.12), transparent 28%),
                radial-gradient(circle at bottom right, rgba(16, 185, 129, 0.08), transparent 24%),
                linear-gradient(180deg, #f8fbff 0%, #eef4fb 100%);
        }

        .block-container {
            max-width: 900px;
            padding-top: 3rem;
            padding-bottom: 2rem;
        }

        h1, h2, h3 {
            color: #0f172a;
            letter-spacing: -0.02em;
        }

        div[data-testid="stForm"] {
            background: rgba(255, 255, 255, 0.80);
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 24px;
            padding: 1.25rem 1.25rem 0.75rem 1.25rem;
            box-shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
        }

        .stTextInput > div > div {
            border-radius: 14px !important;
            border: 1px solid rgba(148, 163, 184, 0.30) !important;
            background: rgba(255,255,255,0.95) !important;
            box-shadow: 0 6px 16px rgba(15, 23, 42, 0.04);
        }

        .stTextInput > div > div:focus-within {
            border-color: rgba(37, 99, 235, 0.50) !important;
            box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.10);
        }

        .stButton > button,
        .stFormSubmitButton > button {
            border-radius: 14px !important;
            border: 1px solid rgba(37, 99, 235, 0.18) !important;
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
            color: white !important;
            font-weight: 700 !important;
            min-height: 2.9rem !important;
            padding: 0.55rem 1.1rem !important;
            box-shadow: 0 12px 22px rgba(37, 99, 235, 0.24);
            transition: all 0.18s ease-in-out;
        }

        .stButton > button:hover,
        .stFormSubmitButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 16px 28px rgba(37, 99, 235, 0.28);
        }

        div[data-testid="stAlert"] {
            border-radius: 18px;
            border: 1px solid rgba(148, 163, 184, 0.20);
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
        }

        header[data-testid="stHeader"] {
            background: rgba(255,255,255,0.75);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div style="
        background: linear-gradient(135deg, #0f172a 0%, #1d4ed8 100%);
        color: white;
        padding: 1.6rem 1.8rem;
        border-radius: 26px;
        box-shadow: 0 18px 40px rgba(15, 23, 42, 0.18);
        margin-bottom: 1.25rem;
    ">
        <div style="font-size: 0.95rem; opacity: 0.85; font-weight: 600;">
            Co-Parent Shared Expenses
        </div>
        <div style="font-size: 2rem; font-weight: 800; margin-top: 0.2rem;">
            Welcome back
        </div>
        <div style="margin-top: 0.45rem; font-size: 1rem; opacity: 0.92;">
            Log in to your shared expense account.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if is_logged_in():
    user = get_current_user()
    st.success(f"You are currently logged in as {user['user_name']}.")
    st.info(f"Household: {user['household_name']}")

    col1, col2, _ = st.columns([1, 1, 2])

    with col1:
        if st.button("Go to Home", type="primary", use_container_width=True):
            st.rerun()

    with col2:
        if st.button("Log Out", use_container_width=True):
            logout_user()
            st.success("You have been logged out.")
            st.rerun()

    st.stop()

left_spacer, main_col, right_spacer = st.columns([1, 1.4, 1])

with main_col:
    with st.form("log_in_form"):
        email = st.text_input("Email", placeholder="name@example.com")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        submitted = st.form_submit_button("Log In", type="primary", use_container_width=True)

    st.markdown(
        """
        <div style="
            margin-top: 1rem;
            padding: 1rem 1.1rem;
            border-radius: 18px;
            background: rgba(255,255,255,0.72);
            border: 1px solid rgba(148,163,184,0.16);
            box-shadow: 0 10px 24px rgba(15,23,42,0.05);
        ">
            <div style="font-weight: 700; color: #0f172a; margin-bottom: 0.35rem;">
                Need access?
            </div>
            <div style="color: #475569;">
                Use the Sign Up page to create an account or enter your invite code.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

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