import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

import streamlit as st
from utils.auth import require_login, logout_user, is_logged_in
import datetime

def render_sidebar_nav():
    with st.sidebar:
        st.page_link("pages/Log_In.py", label="Home")
        st.page_link("pages/01_Summary.py", label="Summary")
        st.page_link("pages/02_Add_Expense.py", label="Add Expense")
        st.page_link("pages/05_Update_Payment.py", label="Update Payment")
        st.page_link("pages/04_Ledger.py", label="Ledger")
        st.page_link("pages/07_Profile.py", label="Profile")

st.set_page_config(
    page_title="Home",
    page_icon="🏠",
    layout="wide"
)

# -----------------------------
# STYLE
# -----------------------------
st.markdown("""
<style>

/* PAGE WIDTH */
.block-container {
    max-width: 900px;
    margin: 0 auto;
    padding-top: 2rem;
}

/* MAIN CARD */
.card {
    max-width: 620px;
    margin: 2rem auto;
    padding: 2rem;
    border-radius: 24px;
    background: rgba(255, 255, 255, 0.94);
    box-shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
    border: 1px solid rgba(226, 232, 240, 0.9);
}

/* CARD TEXT */
.card h3 {
    margin-top: 0;
    margin-bottom: 0.75rem;
    font-size: 1.35rem;
}

.card p {
    color: #475569;
    margin-bottom: 1rem;
}

.card ul {
    margin-top: 0.5rem;
    color: #334155;
    line-height: 1.8;
}

/* BUTTONS */
div.stButton > button {
    width: 100%;
    height: 2.8rem;
    border-radius: 14px;
    font-weight: 700;
    border: 1px solid rgba(148, 163, 184, 0.35);
}

div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #2563eb, #1d4ed8);
    color: white;
    border: none;
}

/* TOP RIGHT LOGOUT BUTTON */
.logout-row div.stButton > button {
    height: 2.35rem;
    border-radius: 999px;
    background: transparent;
    color: #64748b;
    font-size: 0.85rem;
    font-weight: 700;
    border: 1px solid rgba(148, 163, 184, 0.35);
}

.logout-row div.stButton > button:hover {
    color: #dc2626;
    border-color: rgba(220, 38, 38, 0.35);
    background: rgba(254, 242, 242, 0.8);
}

/* FOOTER */
.footer {
    text-align: center;
    margin-top: 40px;
    font-size: 0.8rem;
    color: #94a3b8;
}

</style>
""", unsafe_allow_html=True)


# -----------------------------
# LOGIN GUARD
# -----------------------------
if not is_logged_in():
    st.switch_page("pages/Log_In.py")
user = require_login()
user_name = user.get("user_name", "there")

render_sidebar_nav()


# -----------------------------
# TOP RIGHT LOGOUT
# -----------------------------
st.markdown('<div class="logout-row">', unsafe_allow_html=True)

top_left, top_right = st.columns([5, 1])

with top_right:
    if st.button("Log Out", key="logout_top"):
        logout_user()
        st.switch_page("pages/Log_In.py")

st.markdown('</div>', unsafe_allow_html=True)


# -----------------------------
# HEADER
# -----------------------------
st.title("🏠 Co-Parent Shared Expenses")
st.markdown(f"**Welcome, {user_name}**")


# -----------------------------
# HOME CARD
# -----------------------------
st.markdown("""
<div class="card">
    <h3>Manage shared household expenses in one place</h3>
    <p>Use the sidebar to manage:</p>
    <ul>
        <li>Expenses</li>
        <li>Payments</li>
        <li>Household members</li>
        <li>Summary reports</li>
    </ul>
</div>
""", unsafe_allow_html=True)


# -----------------------------
# PRIMARY ACTION
# -----------------------------
if st.button("Go to Summary", type="primary", use_container_width=True):
    st.switch_page("pages/01_Summary.py")


# -----------------------------
# FOOTER
# -----------------------------
year = datetime.datetime.now().year
st.markdown(
    f'<div class="footer">© {year} Co-Parent Shared Expenses</div>',
    unsafe_allow_html=True
)