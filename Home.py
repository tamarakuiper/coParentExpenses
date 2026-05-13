import streamlit as st

from utils.auth import is_logged_in, get_current_user, logout_user, require_login
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
    st.title("🏠 Co-Parent Shared Expenses")
    st.write("Track shared child-related expenses in one place.")
    st.write("Please log in or sign up to continue.")
    st.caption("If you were invited, use the Sign Up page and enter your invite code there.")


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