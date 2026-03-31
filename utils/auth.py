import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import streamlit as st
from utils.db import get_connection


def normalize_email(email):
    return email.strip().lower()


def get_user_by_email(email):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, full_name, email, password_hash, created_at FROM users WHERE email = ?",
        (normalize_email(email),),
    )
    user = cursor.fetchone()
    conn.close()
    return user


def get_primary_membership(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            hm.household_id,
            hm.user_id,
            hm.role,
            h.name AS household_name
        FROM household_memberships hm
        JOIN households h
            ON h.id = hm.household_id
        WHERE hm.user_id = ?
        ORDER BY hm.id ASC
        LIMIT 1
        """,
        (user_id,),
    )
    membership = cursor.fetchone()
    conn.close()
    return membership


def create_user_with_household(full_name, email, password, household_name):
    cleaned_name = full_name.strip()
    cleaned_email = normalize_email(email)
    cleaned_household_name = household_name.strip()
    password_hash = generate_password_hash(password)

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO users (full_name, email, password_hash)
            VALUES (?, ?, ?)
            """,
            (cleaned_name, cleaned_email, password_hash),
        )
        user_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO households (name, created_by_user_id)
            VALUES (?, ?)
            """,
            (cleaned_household_name, user_id),
        )
        household_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO household_memberships (household_id, user_id, role)
            VALUES (?, ?, ?)
            """,
            (household_id, user_id, "owner"),
        )

        conn.commit()

        return {
            "user_id": user_id,
            "household_id": household_id,
            "role": "owner",
        }

    except sqlite3.IntegrityError as exc:
        conn.rollback()
        if "UNIQUE constraint failed: users.email" in str(exc):
            raise ValueError("An account with that email already exists.") from exc
        raise

    finally:
        conn.close()


def login_user(email, password):
    user = get_user_by_email(email)

    if not user:
        return False, "No account was found for that email."

    if not check_password_hash(user["password_hash"], password):
        return False, "Incorrect password."

    membership = get_primary_membership(user["id"])
    if not membership:
        return False, "This account is not linked to a household yet."

    st.session_state["logged_in"] = True
    st.session_state["user_id"] = user["id"]
    st.session_state["user_name"] = user["full_name"]
    st.session_state["user_email"] = user["email"]
    st.session_state["household_id"] = membership["household_id"]
    st.session_state["household_name"] = membership["household_name"]
    st.session_state["role"] = membership["role"]

    return True, None


def logout_user():
    keys_to_clear = [
        "logged_in",
        "user_id",
        "user_name",
        "user_email",
        "household_id",
        "household_name",
        "role",
    ]
    for key in keys_to_clear:
        st.session_state.pop(key, None)


def is_logged_in():
    return st.session_state.get("logged_in", False)


def get_current_user():
    if not is_logged_in():
        return None

    return {
        "user_id": st.session_state.get("user_id"),
        "user_name": st.session_state.get("user_name"),
        "user_email": st.session_state.get("user_email"),
        "household_id": st.session_state.get("household_id"),
        "household_name": st.session_state.get("household_name"),
        "role": st.session_state.get("role"),
    }


def require_login():
    user = get_current_user()
    if not user:
        st.warning("Please log in to use this page.")
        st.stop()
    return user