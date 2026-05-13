import streamlit as st

from utils.auth import is_logged_in, get_current_user, logout_user, require_login
from utils.db import get_connection
from utils.invites import create_household_invite
from utils.household_admin import fetch_household_members, remove_household_member
from utils.emailer import send_household_invite_email
from datetime import datetime
import os

BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8501")

##BASE_URL = "https://coparentexpenses-production.up.railway.app"

st.set_page_config(
    page_title="Co-Parent Shared Expenses",
    page_icon="🏠",
    layout="wide",
)

st.markdown(
    """
    <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(37, 99, 235, 0.10), transparent 28%),
                radial-gradient(circle at top right, rgba(16, 185, 129, 0.08), transparent 24%),
                linear-gradient(180deg, #f8fbff 0%, #eef4fb 100%);
        }

        .block-container {
            max-width: 1180px;
            padding-top: 2.2rem;
            padding-bottom: 2rem;
        }

        h1, h2, h3 {
            color: #0f172a;
            letter-spacing: -0.02em;
        }

        h1 {
            font-size: 2.35rem !important;
            font-weight: 800 !important;
            margin-bottom: 0.5rem !important;
        }

        h2, h3 {
            font-weight: 700 !important;
        }

        p, li, label, .stMarkdown, .stCaption {
            color: #334155;
        }

        hr {
            border: none;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(100,116,139,0.35), transparent);
            margin-top: 1.4rem;
            margin-bottom: 1.4rem;
        }

        div[data-testid="stAlert"] {
            border-radius: 18px;
            border: 1px solid rgba(148, 163, 184, 0.20);
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
            padding: 0.85rem 1rem;
        }

        .stButton > button,
        .stDownloadButton > button,
        .stFormSubmitButton > button {
            border-radius: 14px !important;
            border: 1px solid rgba(37, 99, 235, 0.18) !important;
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
            color: white !important;
            font-weight: 700 !important;
            min-height: 2.8rem !important;
            padding: 0.55rem 1.1rem !important;
            box-shadow: 0 10px 18px rgba(37, 99, 235, 0.22);
            transition: all 0.18s ease-in-out;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover,
        .stFormSubmitButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 14px 24px rgba(37, 99, 235, 0.28);
            border-color: rgba(37, 99, 235, 0.28) !important;
        }

        .stButton > button:active,
        .stDownloadButton > button:active,
        .stFormSubmitButton > button:active {
            transform: translateY(0px);
        }

        .stButton > button[kind="secondary"] {
            background: white !important;
            color: #1e3a8a !important;
            border: 1px solid rgba(37, 99, 235, 0.22) !important;
            box-shadow: 0 8px 16px rgba(15, 23, 42, 0.06);
        }

        .stButton > button[kind="secondary"]:hover {
            background: #eff6ff !important;
        }

        .stTextInput > div > div,
        .stSelectbox > div > div,
        .stTextArea > div > div,
        .stDateInput > div > div,
        .stNumberInput > div > div {
            border-radius: 14px !important;
            border: 1px solid rgba(148, 163, 184, 0.32) !important;
            background: rgba(255, 255, 255, 0.90) !important;
            box-shadow: 0 6px 16px rgba(15, 23, 42, 0.04);
        }

        .stTextInput > div > div:focus-within,
        .stSelectbox > div > div:focus-within,
        .stTextArea > div > div:focus-within,
        .stDateInput > div > div:focus-within,
        .stNumberInput > div > div:focus-within {
            border-color: rgba(37, 99, 235, 0.50) !important;
            box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.10);
        }

        .stCheckbox {
            padding-top: 0.25rem;
            padding-bottom: 0.25rem;
        }

        div[data-testid="stForm"] {
            background: rgba(255, 255, 255, 0.72);
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 22px;
            padding: 1.1rem 1.1rem 0.6rem 1.1rem;
            box-shadow: 0 14px 32px rgba(15, 23, 42, 0.07);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            margin-bottom: 1rem;
        }

        div[data-testid="stPageLink"] a {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.7rem 0.95rem;
            border-radius: 14px;
            text-decoration: none !important;
            font-weight: 700;
            color: #1d4ed8 !important;
            background: rgba(255,255,255,0.78);
            border: 1px solid rgba(37, 99, 235, 0.14);
            box-shadow: 0 8px 18px rgba(15, 23, 42, 0.05);
            transition: all 0.18s ease;
        }

        div[data-testid="stPageLink"] a:hover {
            background: #eff6ff;
            border-color: rgba(37, 99, 235, 0.24);
            transform: translateY(-1px);
        }

        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0f172a 0%, #172554 100%);
            border-right: 1px solid rgba(255,255,255,0.06);
        }

        section[data-testid="stSidebar"] * {
            color: #e5eefc !important;
        }

        section[data-testid="stSidebar"] .stPageLink a,
        section[data-testid="stSidebar"] a {
            border-radius: 12px !important;
        }

        section[data-testid="stSidebar"] .stPageLink a:hover,
        section[data-testid="stSidebar"] a:hover {
            background: rgba(255,255,255,0.08) !important;
        }

        header[data-testid="stHeader"] {
            background: rgba(255,255,255,0.75);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
        }

        .stSelectbox label,
        .stTextInput label,
        .stCheckbox label {
            font-weight: 600 !important;
            color: #1e293b !important;
        }

        div[data-testid="stMarkdownContainer"] p {
            line-height: 1.6;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


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


def get_payment_profile(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT venmo_handle, zelle_email, zelle_phone
        FROM users
        WHERE id = ?
        LIMIT 1
        """,
        (user_id,),
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return {
            "venmo_handle": "",
            "zelle_email": "",
            "zelle_phone": "",
        }

    try:
        return {
            "venmo_handle": row["venmo_handle"] or "",
            "zelle_email": row["zelle_email"] or "",
            "zelle_phone": row["zelle_phone"] or "",
        }
    except Exception:
        return {
            "venmo_handle": row[0] or "",
            "zelle_email": row[1] or "",
            "zelle_phone": row[2] or "",
        }


def get_household_members_with_last_login(household_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            hm.user_id,
            hm.role,
            hm.joined_at,
            u.full_name,
            u.email,
            u.last_login_at
        FROM household_members hm
        JOIN users u
            ON u.id = hm.user_id
        WHERE hm.household_id = ?
        ORDER BY
            CASE WHEN hm.role = 'owner' THEN 0 ELSE 1 END,
            u.full_name ASC
        """,
        (household_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def format_last_login(value):
    if not value:
        return "Never"

    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").strftime("%b %d, %Y %I:%M %p")
    except Exception:
        return str(value)


def render_logged_out_home():
    st.title("🏠 Co-Parent Shared Expenses")
    st.write("Track shared child-related expenses in one place.")
    st.write("Please log in or sign up to continue.")
    st.caption("If you were invited, use the Sign Up page and enter your invite code there.")


def render_logged_in_home():
    current_user = require_login()
    current_user_email = get_current_user_email(current_user["user_id"])

    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #0f172a 0%, #1d4ed8 100%);
            color: white;
            padding: 1.4rem 1.6rem;
            border-radius: 24px;
            box-shadow: 0 18px 40px rgba(15, 23, 42, 0.18);
            margin-bottom: 1rem;
        ">
            <div style="font-size: 0.95rem; opacity: 0.85; font-weight: 600;">Co-Parent Shared Expenses</div>
            <div style="font-size: 2rem; font-weight: 800; margin-top: 0.2rem;">Welcome, {current_user['user_name']}</div>
            <div style="margin-top: 0.45rem; font-size: 1rem; opacity: 0.92;">
                Household: {current_user['household_name']}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    payment_profile = get_payment_profile(current_user["user_id"])
    has_payment_details = any(
        [
            payment_profile["venmo_handle"].strip(),
            payment_profile["zelle_email"].strip(),
            payment_profile["zelle_phone"].strip(),
        ]
    )

    if not has_payment_details:
        st.warning(
            "You have not added any payment details yet. Add your Venmo or Zelle info in Profile so other household members know how to reimburse you."
        )
        st.page_link("pages/9_Profile.py", label="Go to Profile", icon="👤")

    is_owner = current_user.get("role") == "owner"

    if is_owner:
        st.markdown("---")
        st.subheader("Invite another user")

        with st.form("invite_user_form"):
            invited_email = st.text_input("Invitee Email", placeholder="name@example.com")
            submitted = st.form_submit_button("Create Invite", type="primary")

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

                    send_household_invite_email(
                        to_email=normalized_invited_email,
                        inviter_name=current_user["user_name"],
                        household_name=current_user.get("household_name", "your household"),
                        token=token,
                    )

                    st.success(f"Invite emailed to {normalized_invited_email}.")

                except ValueError as exc:
                    st.error(str(exc))
                except Exception as exc:
                    st.error(f"Something went wrong while creating or sending the invite: {exc}")

        st.markdown("---")
        st.subheader("Manage household")

        members = get_household_members_with_last_login(current_user["household_id"])

        removable_members = []
        for member in members:
            try:
                member_user_id = member["user_id"]
                member_name = member["full_name"]
                member_email = member["email"]
                member_role = member["role"]
                member_last_login = member["last_login_at"]
            except Exception:
                member_user_id = member[0]
                member_role = member[1]
                member_name = member[3]
                member_email = member[4]
                member_last_login = member[5]

            formatted_last_login = format_last_login(member_last_login)
            label = f"{member_name} ({member_email}) — {member_role} • Last login: {formatted_last_login}"
            st.write(label)

            if member_user_id != current_user["user_id"] and member_role != "owner":
                removable_members.append(
                    {
                        "user_id": member_user_id,
                        "label": f"{member_name} ({member_email}) — {member_role}",
                    }
                )

        if not removable_members:
            st.info("There are no removable members in this household.")
        else:
            options = {item["label"]: item["user_id"] for item in removable_members}

            selected_label = st.selectbox(
                "Select a household member to remove",
                list(options.keys()),
                key="remove_member_select",
            )

            confirm_remove = st.checkbox(
                "I understand this will remove this user's access to the household.",
                key="confirm_remove_member",
            )

            if st.button("Remove User", type="secondary"):
                if not confirm_remove:
                    st.error("Please confirm removal first.")
                else:
                    target_user_id = options[selected_label]
                    ok, message = remove_household_member(
                        household_id=current_user["household_id"],
                        acting_user_id=current_user["user_id"],
                        target_user_id=target_user_id,
                    )

                    if ok:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
    else:
        st.markdown("---")
        st.info("Only the household owner can invite or remove household members.")


def render_home():
    if is_logged_in():
        render_logged_in_home()
    else:
        render_logged_out_home()


def render_logout():
    st.title("🚪 Log Out")
    logout_user()
    st.success("You have been logged out.")
    st.rerun()


home_page = st.Page(render_home, title="Home", icon="🏠", default=True)
profile_page = st.Page("pages/9_Profile.py", title="Profile", icon="👤")

login_page = st.Page("pages/02_Log_In.py", title="Login", icon="🔐")
signup_page = st.Page("pages/01_Sign_Up.py", title="Signup", icon="🆕")

summary_page = st.Page("pages/4_Summary.py", title="Summary", icon="📊")
add_expense_page = st.Page("pages/1_Add_Expense.py", title="Add Expense", icon="🧾")
ledger_page = st.Page("pages/2_Ledger.py", title="Ledger", icon="📒")
update_payment_page = st.Page("pages/3_Update_Payment.py", title="Update Payment", icon="💳")
logout_page = st.Page(render_logout, title="Log Out", icon="🚪")

if is_logged_in():
    pages = [
        home_page,
        summary_page,
        add_expense_page,
        ledger_page,
        update_payment_page,
        profile_page,
        logout_page,
    ]
    nav_position = "sidebar"
else:
    pages = [
        home_page,
        login_page,
        signup_page,
    ]
    nav_position = "top"

pg = st.navigation(pages, position=nav_position)
pg.run()