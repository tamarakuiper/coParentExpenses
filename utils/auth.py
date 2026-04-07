import streamlit as st
from werkzeug.security import generate_password_hash, check_password_hash

from utils.db import get_connection


def _row_get(row, key, default=None):
    if row is None:
        return default
    try:
        return row[key]
    except Exception:
        return default


def get_primary_membership(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            hm.household_id,
            hm.role,
            h.name AS household_name,
            h.created_by_user_id
        FROM household_members hm
        JOIN households h
            ON h.id = hm.household_id
        WHERE hm.user_id = ?
        ORDER BY
            CASE WHEN hm.role = 'owner' THEN 0 ELSE 1 END,
            hm.id ASC
        LIMIT 1
        """,
        (user_id,),
    )

    row = cursor.fetchone()
    conn.close()
    return row


def create_user(full_name, email, password):
    full_name = (full_name or "").strip()
    email = (email or "").strip().lower()

    if not full_name:
        raise ValueError("Full Name is required.")
    if not email:
        raise ValueError("Email is required.")
    if not password:
        raise ValueError("Password is required.")
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id
        FROM users
        WHERE lower(email) = lower(?)
        """,
        (email,),
    )
    existing_user = cursor.fetchone()
    if existing_user:
        conn.close()
        raise ValueError("An account with that email already exists.")

    password_hash = generate_password_hash(password)

    cursor.execute(
        """
        INSERT INTO users (full_name, email, password_hash)
        VALUES (?, ?, ?)
        """,
        (full_name, email, password_hash),
    )
    user_id = cursor.lastrowid

    conn.commit()
    conn.close()
    return user_id


def create_user_with_household(full_name, email, password, household_name):
    household_name = (household_name or "").strip()
    if not household_name:
        raise ValueError("Household Name is required.")

    user_id = create_user(full_name, email, password)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO households (name, created_by_user_id)
        VALUES (?, ?)
        """,
        (household_name, user_id),
    )
    household_id = cursor.lastrowid

    cursor.execute(
        """
        INSERT INTO household_members (household_id, user_id, role)
        VALUES (?, ?, 'owner')
        """,
        (household_id, user_id),
    )

    conn.commit()
    conn.close()
    return user_id


def login_user(email, password):
    email = (email or "").strip().lower()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, full_name, email, password_hash
        FROM users
        WHERE lower(email) = lower(?)
        LIMIT 1
        """,
        (email,),
    )
    user = cursor.fetchone()

    if not user:
        conn.close()
        return False, "No account found for that email."

    if not check_password_hash(_row_get(user, "password_hash"), password):
        conn.close()
        return False, "Incorrect password."

    membership = get_primary_membership(_row_get(user, "id"))
    if not membership:
        conn.close()
        return False, "This user is not assigned to a household."

    cursor.execute(
        """
        UPDATE users
        SET last_login_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (_row_get(user, "id"),),
    )
    conn.commit()
    conn.close()

    role = _row_get(membership, "role")
    is_household_owner = role == "owner"

    st.session_state["logged_in"] = True
    st.session_state["user_id"] = _row_get(user, "id")
    st.session_state["user_name"] = _row_get(user, "full_name")
    st.session_state["email"] = _row_get(user, "email")
    st.session_state["household_id"] = _row_get(membership, "household_id")
    st.session_state["household_name"] = _row_get(membership, "household_name")
    st.session_state["role"] = role
    st.session_state["is_household_owner"] = is_household_owner

    return True, None


def logout_user():
    for key in [
        "logged_in",
        "user_id",
        "user_name",
        "email",
        "household_id",
        "household_name",
        "role",
        "is_household_owner",
    ]:
        st.session_state.pop(key, None)


def is_logged_in():
    return bool(st.session_state.get("logged_in"))


def get_current_user():
    if not is_logged_in():
        return None

    return {
        "user_id": st.session_state.get("user_id"),
        "user_name": st.session_state.get("user_name"),
        "email": st.session_state.get("email"),
        "household_id": st.session_state.get("household_id"),
        "household_name": st.session_state.get("household_name"),
        "role": st.session_state.get("role"),
        "is_household_owner": bool(st.session_state.get("is_household_owner")),
    }


def require_login():
    user = get_current_user()
    if not user:
        st.warning("Please log in first.")
        st.stop()
    return user