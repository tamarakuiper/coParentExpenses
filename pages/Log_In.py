import streamlit as st
from utils.auth import login_user, is_logged_in
import datetime

st.set_page_config(page_title="Log In", page_icon="🔐", layout="wide")

st.markdown("""
<style>

/* GLOBAL PAGE */
.stApp {
    background:
        radial-gradient(circle at top left, rgba(99, 102, 241, 0.22), transparent 34%),
        radial-gradient(circle at bottom right, rgba(14, 165, 233, 0.20), transparent 30%),
        linear-gradient(135deg, #f8fafc 0%, #eef2ff 45%, #f0f9ff 100%);
}

/* PAGE WIDTH */
.block-container {
    max-width: 980px;
    margin: 0 auto;
    padding-top: 4rem;
}

/* HIDE STREAMLIT FORM WRAPPER */
div[data-testid="stForm"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}

/* LOGIN CARD */
div[data-testid="stVerticalBlock"] > div:has(> div[data-testid="stForm"]) {
    max-width: 540px;
    margin: 35px auto 18px auto;
    padding: 2.4rem 2.3rem 2.2rem 2.3rem;
    border-radius: 28px;
    background: rgba(255, 255, 255, 0.92);
    border: 1px solid rgba(226, 232, 240, 0.9);
    box-shadow:
        0 24px 70px rgba(15, 23, 42, 0.13),
        inset 0 1px 0 rgba(255, 255, 255, 0.8);
    backdrop-filter: blur(14px);
}

/* SIGNUP CARD */
div[data-testid="stVerticalBlock"] > div:has(button[kind="secondary"]) {
    max-width: 540px;
    margin: 18px auto;
    padding: 1.35rem 1.5rem;
    border-radius: 22px;
    background: rgba(255, 255, 255, 0.78);
    border: 1px solid rgba(226, 232, 240, 0.85);
    box-shadow: 0 14px 36px rgba(15, 23, 42, 0.08);
    backdrop-filter: blur(12px);
}

/* BRAND HEADER */
.auth-badge {
    width: fit-content;
    margin: 0 auto 1rem auto;
    padding: 0.45rem 0.8rem;
    border-radius: 999px;
    background: #eef2ff;
    color: #4338ca;
    font-size: 0.78rem;
    font-weight: 800;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

.auth-icon {
    width: 64px;
    height: 64px;
    margin: 0 auto 1rem auto;
    border-radius: 22px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #4f46e5, #0ea5e9);
    color: white;
    font-size: 1.8rem;
    box-shadow: 0 14px 30px rgba(79, 70, 229, 0.28);
}

.auth-title {
    text-align: center;
    font-size: 2.25rem;
    line-height: 1.1;
    font-weight: 900;
    color: #0f172a;
    letter-spacing: -0.04em;
    margin-bottom: 0.55rem;
}

.auth-subtitle {
    text-align: center;
    color: #64748b;
    margin: 0 auto 1.6rem auto;
    max-width: 410px;
    font-size: 0.98rem;
}

/* INPUT LABELS */
label {
    color: #334155 !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
}

/* INPUT FIELDS */
div[data-testid="stTextInput"] div[data-baseweb="input"] {
    height: 46px;
    border-radius: 15px;
    border: 1px solid #cbd5e1;
    background: #f8fafc;
    transition: all 0.18s ease;
}

div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within {
    border-color: #6366f1;
    background: white;
    box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.14);
}

div[data-testid="stTextInput"] input {
    padding-right: 2.8rem;
    color: #0f172a;
}

/* PASSWORD ICON ALIGNMENT */
button[data-testid="stPasswordVisibilityToggle"] {
    position: absolute;
    right: 0.6rem;
    top: 50%;
    transform: translateY(-50%);
}

/* LOGIN BUTTON */
.stFormSubmitButton > button {
    width: 100%;
    height: 2.95rem;
    margin-top: 0.85rem;
    border-radius: 16px;
    border: none;
    background: linear-gradient(135deg, #4f46e5, #0ea5e9);
    color: white;
    font-weight: 800;
    box-shadow: 0 12px 28px rgba(79, 70, 229, 0.28);
    transition: all 0.18s ease;
}

.stFormSubmitButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 16px 34px rgba(79, 70, 229, 0.35);
    color: white;
}

/* SIGNUP BUTTON */
div[data-testid="stVerticalBlock"] > div:has(button[kind="secondary"]) button {
    border-radius: 15px;
    height: 2.8rem;
    font-weight: 800;
    border: 1px solid #c7d2fe;
    color: #4338ca;
    background: #eef2ff;
    transition: all 0.18s ease;
}

div[data-testid="stVerticalBlock"] > div:has(button[kind="secondary"]) button:hover {
    background: #e0e7ff;
    border-color: #a5b4fc;
    transform: translateY(-1px);
}

/* STATUS MESSAGES */
div[data-testid="stAlert"] {
    max-width: 540px;
    margin: 1rem auto;
    border-radius: 16px;
}

/* HELPERS */
.center {
    text-align: center;
    color: #475569;
    margin-bottom: 0.8rem;
}

.center strong {
    color: #0f172a;
}

/* FOOTER */
.footer {
    text-align: center;
    margin-top: 2.25rem;
    font-size: 0.82rem;
    color: #94a3b8;
}

/* MOBILE */
@media (max-width: 640px) {
    .block-container {
        padding-top: 2rem;
    }

    div[data-testid="stVerticalBlock"] > div:has(> div[data-testid="stForm"]) {
        margin-top: 20px;
        padding: 1.8rem 1.4rem;
        border-radius: 24px;
    }

    .auth-title {
        font-size: 1.8rem;
    }
}

</style>
""", unsafe_allow_html=True)


# Already logged in
if is_logged_in():
    st.success("You are already logged in.")
    if st.button("Go to Home"):
        st.switch_page("Home.py")
    st.stop()


# LOGIN FORM
login_card = st.container()

with login_card:
    with st.form("login_form"):
        st.markdown("""
            <div class="auth-badge">Secure family expense tracking</div>
            <div class="auth-icon">🔐</div>
            <div class="auth-title">Co-Parent Shared Expenses</div>
            <div class="auth-subtitle">
                Log in to track expenses, payments, and shared balances with less friction.
            </div>
        """, unsafe_allow_html=True)

        email = st.text_input("Email", placeholder="name@example.com")
        password = st.text_input("Password", type="password", placeholder="Enter your password")

        submitted = st.form_submit_button("Log In")


# LOGIN LOGIC
if submitted:
    if not email.strip():
        st.error("Email is required.")
    elif not password:
        st.error("Password is required.")
    else:
        success, msg = login_user(email.strip(), password)
        if success:
            st.switch_page("Home.py")
        else:
            st.error(msg)


# SIGNUP CARD
signup_card = st.container()

with signup_card:
    st.markdown(
        '<div class="center"><strong>New here?</strong> Create an account to start tracking shared expenses.</div>',
        unsafe_allow_html=True
    )

    if st.button("🆕 Create account", use_container_width=True):
        st.switch_page("pages/Sign_Up.py")


# FOOTER
year = datetime.datetime.now().year
st.markdown(
    f'<div class="footer">© {year} Co-Parent Shared Expenses · Built for clarity and accountability</div>',
    unsafe_allow_html=True
)