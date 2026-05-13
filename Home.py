import streamlit as st

from utils.auth import is_logged_in, get_current_user, logout_user, require_login, login_user
from utils.db import get_connection
from utils.invites import create_household_invite
from utils.household_admin import fetch_household_members, remove_household_member
from utils.household_children import (
    seed_default_children_if_empty,
    save_household_child_names,
    normalize_expense_child_names,
    fetch_unmapped_expense_child_names,
    remap_expense_child_name,
)
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
    st.markdown(
        """
        <style>
            .stApp {
                background:
                    radial-gradient(circle at 20% 10%, rgba(37, 99, 235, 0.16), transparent 28%),
                    radial-gradient(circle at 80% 85%, rgba(20, 184, 166, 0.13), transparent 28%),
                    linear-gradient(135deg, #f8fbff 0%, #eef5ff 48%, #f8fafc 100%);
            }

            header[data-testid="stHeader"] {
                background: rgba(255,255,255,0.72);
                backdrop-filter: blur(10px);
                -webkit-backdrop-filter: blur(10px);
            }

            .block-container {
                max-width: 560px !important;
                padding-top: 13vh !important;
                padding-bottom: 4rem !important;
                margin-left: auto !important;
                margin-right: auto !important;
            }

            .login-card-top {
                padding: 2rem 2rem 1.1rem 2rem;
                border-radius: 30px 30px 0 0;
                background: rgba(255, 255, 255, 0.90);
                border-top: 1px solid rgba(148, 163, 184, 0.24);
                border-left: 1px solid rgba(148, 163, 184, 0.24);
                border-right: 1px solid rgba(148, 163, 184, 0.24);
                box-shadow: 0 24px 70px rgba(15, 23, 42, 0.12);
                backdrop-filter: blur(14px);
                -webkit-backdrop-filter: blur(14px);
            }

            .login-badge {
                width: 54px;
                height: 54px;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 1rem auto;
                border-radius: 18px;
                background: linear-gradient(135deg, #2563eb 0%, #14b8a6 100%);
                color: white;
                font-size: 1.7rem;
                box-shadow: 0 14px 26px rgba(37, 99, 235, 0.22);
            }

            .login-title {
                margin: 0;
                text-align: center;
                color: #0f172a;
                font-size: 2rem;
                line-height: 1.15;
                font-weight: 800;
                letter-spacing: -0.04em;
            }

            .login-subtitle {
                margin: 0.55rem auto 0 auto;
                text-align: center;
                color: #475569;
                font-size: 1rem;
                max-width: 360px;
            }

            div[data-testid="stForm"] {
                margin-top: -1px;
                padding: 0 2rem 1.7rem 2rem;
                border-radius: 0 0 30px 30px;
                background: rgba(255, 255, 255, 0.90);
                border-top: 0;
                border-left: 1px solid rgba(148, 163, 184, 0.24);
                border-right: 1px solid rgba(148, 163, 184, 0.24);
                border-bottom: 1px solid rgba(148, 163, 184, 0.24);
                box-shadow: 0 24px 70px rgba(15, 23, 42, 0.12);
                backdrop-filter: blur(14px);
                -webkit-backdrop-filter: blur(14px);
            }

            .stTextInput label {
                color: #334155 !important;
                font-weight: 700 !important;
            }

            .stTextInput > div > div {
                border-radius: 15px !important;
                border: 1px solid rgba(148, 163, 184, 0.36) !important;
                background: rgba(255,255,255,0.96) !important;
                box-shadow: 0 8px 18px rgba(15, 23, 42, 0.05);
            }

            .stTextInput > div > div:focus-within {
                border-color: rgba(37, 99, 235, 0.62) !important;
                box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.10);
            }

            .stFormSubmitButton > button {
                width: 100%;
                min-height: 3rem;
                border-radius: 16px !important;
                border: 0 !important;
                background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
                color: white !important;
                font-weight: 800 !important;
                box-shadow: 0 16px 30px rgba(37, 99, 235, 0.26);
                transition: all 0.18s ease-in-out;
            }

            .stFormSubmitButton > button:hover {
                transform: translateY(-1px);
                box-shadow: 0 20px 38px rgba(37, 99, 235, 0.30);
            }

            div[data-testid="stAlert"] {
                border-radius: 16px;
                border: 1px solid rgba(148, 163, 184, 0.22);
                box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
            }

            .signup-link-card {
                margin-top: 1rem;
                padding: 1rem 1.25rem;
                text-align: center;
                color: #475569;
                font-size: 0.96rem;
                border-radius: 22px;
                background: rgba(255, 255, 255, 0.74);
                border: 1px solid rgba(148, 163, 184, 0.20);
                box-shadow: 0 12px 30px rgba(15, 23, 42, 0.07);
            }

            .signup-link-card a {
                color: #1d4ed8;
                font-weight: 800;
                text-decoration: none;
            }

            .signup-link-card a:hover {
                text-decoration: underline;
            }

            div[data-testid="stPageLink"] {
                display: flex;
                justify-content: center;
            }

            div[data-testid="stPageLink"] a {
                justify-content: center;
                border-radius: 14px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="login-card-top">
            <div class="login-badge">🏠</div>
            <h1 class="login-title">Co-Parent Shared Expenses</h1>
            <p class="login-subtitle">Log in to track expenses, payments, receipts, and household balances in one shared place.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("home_log_in_form"):
        email = st.text_input("Email", placeholder="name@example.com")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        submitted = st.form_submit_button("Log In", type="primary")

    if submitted:
        if not email.strip():
            st.error("Email is required.")
        elif not password:
            st.error("Password is required.")
        else:
            success, error_message = login_user(email.strip().lower(), password)
            if success:
                st.rerun()
            else:
                st.error(error_message)

    st.markdown(
        """
        <div class="signup-link-card">
            <strong>New to Co-Parent Shared Expenses?</strong>
        """,
        unsafe_allow_html=True,
    )
    st.page_link("pages/01_Sign_Up.py", label="Create an account", icon="🆕")
    st.caption("Invited users can sign up with their invite code.")
    st.markdown("</div>", unsafe_allow_html=True)

def render_logged_in_home():
    current_user = require_login()
    current_user_email = get_current_user_email(current_user["user_id"])

    st.title("🏠 Co-Parent Shared Expenses")
    st.success(f"Logged in as {current_user['user_name']}")
    st.info(f"Household: {current_user['household_name']}")
    st.write("Use the menu on the left to manage your household expenses.")

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
        st.subheader("Manage household children")
        st.write("These names appear in the Child dropdown when adding or editing expenses.")

        current_child_names = seed_default_children_if_empty(current_user["household_id"])
        child_names_text = st.text_area(
            "Children",
            value="\n".join(current_child_names),
            help="Enter one child name per line.",
            key="household_children_text",
        )

        if st.button("Save Children", type="primary"):
            child_names = [line.strip() for line in child_names_text.splitlines() if line.strip()]
            if not child_names:
                st.error("Add at least one child name.")
            else:
                saved_names = save_household_child_names(current_user["household_id"], child_names)
                normalized_count = normalize_expense_child_names(current_user["household_id"], saved_names)
                message = "Household children updated: " + ", ".join(saved_names)
                if normalized_count:
                    message += f". Also updated {normalized_count} existing expense row(s) to match the saved spelling."
                st.success(message)
                st.rerun()

        household_child_names = seed_default_children_if_empty(current_user["household_id"])
        unmapped_child_names = fetch_unmapped_expense_child_names(
            current_user["household_id"],
            household_child_names,
        )

        if unmapped_child_names:
            st.warning(
                "Some existing expenses use child names that are not in your household child list. "
                "Map them below so the Ledger does not show duplicate children."
            )

            with st.form("map_existing_expense_children"):
                mappings = {}
                for old_name in unmapped_child_names:
                    mappings[old_name] = st.selectbox(
                        f"Map existing expenses for '{old_name}' to",
                        household_child_names,
                        key=f"map_child_{old_name}",
                    )

                submitted_mappings = st.form_submit_button("Update Existing Expenses", type="primary")

            if submitted_mappings:
                total_updated = 0
                for old_name, new_name in mappings.items():
                    if old_name != new_name:
                        total_updated += remap_expense_child_name(
                            current_user["household_id"],
                            old_name,
                            new_name,
                        )

                st.success(f"Updated {total_updated} existing expense row(s).")
                st.rerun()
        else:
            st.caption("Existing expense child names are already matched to the household child list.")

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