import streamlit as st

from utils.auth import is_logged_in, get_current_user, logout_user, require_login
from utils.db import get_connection
from utils.invites import create_household_invite
from utils.household_admin import fetch_household_members, remove_household_member

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
                    invited_email=invited_email,
                    invited_by_user_id=current_user["user_id"],
                )

                signup_link = f"http://localhost:8501/Sign_Up?invite={token}"

                st.success("Invite created.")
                st.write("Share this sign-up link:")
                st.code(signup_link)

                st.write("Or share this invite code:")
                st.code(token)

             

            except ValueError as exc:
                st.error(str(exc))
            except Exception as exc:
                st.error(f"Something went wrong while creating the invite: {exc}")
        st.markdown("---")
    st.subheader("Manage household")

    members = fetch_household_members(current_user["household_id"])

    removable_members = []
    for member in members:
        try:
            member_user_id = member["user_id"]
            member_name = member["full_name"]
            member_email = member["email"]
            member_role = member["role"]
        except Exception:
            member_user_id = member[0]
            member_role = member[1]
            member_name = member[3]
            member_email = member[4]

        label = f"{member_name} ({member_email}) — {member_role}"
        st.write(label)

        if current_user.get("role") == "owner" and member_user_id != current_user["user_id"] and member_role != "owner":
            removable_members.append(
                {
                    "user_id": member_user_id,
                    "label": label,
                }
            )

    if current_user.get("role") != "owner":
        st.info("Only the household owner can manage members.")
    elif not removable_members:
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