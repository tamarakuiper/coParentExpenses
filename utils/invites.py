import secrets
import sqlite3
from datetime import datetime, timedelta, timezone

from utils.db import get_connection


def _utc_now():
    return datetime.now(timezone.utc)


def _parse_datetime(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def get_user_household(conn, user_id):
    return conn.execute(
        """
        SELECT household_id, role
        FROM household_members
        WHERE user_id = ?
        LIMIT 1
        """,
        (user_id,),
    ).fetchone()


def create_household_invite(invited_email, invited_by_user_id, expires_in_days=7):
    invited_email = invited_email.strip().lower()
    if not invited_email:
        raise ValueError("Invite email is required.")

    conn = get_connection()

    inviter_membership = get_user_household(conn, invited_by_user_id)
    if not inviter_membership:
        conn.close()
        raise ValueError("Inviting user is not assigned to a household.")

    household_id = inviter_membership["household_id"] if isinstance(inviter_membership, sqlite3.Row) else inviter_membership[0]

    existing_pending = conn.execute(
        """
        SELECT id, token, expires_at
        FROM household_invites
        WHERE household_id = ?
          AND invited_email = ?
          AND status = 'pending'
        ORDER BY id DESC
        LIMIT 1
        """,
        (household_id, invited_email),
    ).fetchone()

    if existing_pending:
        expires_at = existing_pending["expires_at"] if isinstance(existing_pending, sqlite3.Row) else existing_pending[2]
        dt = _parse_datetime(expires_at)
        if dt and dt > _utc_now():
            token = existing_pending["token"] if isinstance(existing_pending, sqlite3.Row) else existing_pending[1]
            conn.close()
            return token

    token = secrets.token_urlsafe(24)
    expires_at = (_utc_now() + timedelta(days=expires_in_days)).isoformat()

    conn.execute(
        """
        INSERT INTO household_invites (
            household_id,
            invited_email,
            invited_by_user_id,
            token,
            status,
            expires_at
        )
        VALUES (?, ?, ?, ?, 'pending', ?)
        """,
        (household_id, invited_email, invited_by_user_id, token, expires_at),
    )
    conn.commit()
    conn.close()
    return token


def get_invite_by_token(token):
    conn = get_connection()
    invite = conn.execute(
        """
        SELECT
            hi.id,
            hi.household_id,
            hi.invited_email,
            hi.invited_by_user_id,
            hi.token,
            hi.status,
            hi.expires_at,
            hi.created_at,
            hi.accepted_by_user_id,
            h.name AS household_name,
            inviter.full_name AS inviter_name
        FROM household_invites hi
        JOIN households h
          ON h.id = hi.household_id
        JOIN users inviter
          ON inviter.id = hi.invited_by_user_id
        WHERE hi.token = ?
        LIMIT 1
        """,
        (token,),
    ).fetchone()
    conn.close()
    return invite


def accept_household_invite(token, current_user_id, current_user_email):
    current_user_email = current_user_email.strip().lower()

    conn = get_connection()
    invite = conn.execute(
        """
        SELECT
            id,
            household_id,
            invited_email,
            status,
            expires_at
        FROM household_invites
        WHERE token = ?
        LIMIT 1
        """,
        (token,),
    ).fetchone()

    if not invite:
        conn.close()
        return False, "Invite not found."

    invite_id = invite["id"] if isinstance(invite, sqlite3.Row) else invite[0]
    household_id = invite["household_id"] if isinstance(invite, sqlite3.Row) else invite[1]
    invited_email = invite["invited_email"] if isinstance(invite, sqlite3.Row) else invite[2]
    status = invite["status"] if isinstance(invite, sqlite3.Row) else invite[3]
    expires_at = invite["expires_at"] if isinstance(invite, sqlite3.Row) else invite[4]

    if status != "pending":
        conn.close()
        return False, "This invite is no longer valid."

    if invited_email.lower() != current_user_email:
        conn.close()
        return False, "This invite was sent to a different email address."

    expires_dt = _parse_datetime(expires_at)
    if expires_dt and expires_dt <= _utc_now():
        conn.execute(
            """
            UPDATE household_invites
            SET status = 'expired'
            WHERE id = ?
            """,
            (invite_id,),
        )
        conn.commit()
        conn.close()
        return False, "This invite has expired."

    existing_membership = get_user_household(conn, current_user_id)
    if existing_membership:
        existing_household_id = existing_membership["household_id"] if isinstance(existing_membership, sqlite3.Row) else existing_membership[0]

        if existing_household_id == household_id:
            conn.execute(
                """
                UPDATE household_invites
                SET status = 'accepted',
                    accepted_by_user_id = ?
                WHERE id = ?
                """,
                (current_user_id, invite_id),
            )
            conn.commit()
            conn.close()
            return True, "You are already in this household."

        existing_expense_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM expenses
            WHERE household_id = ?
              AND created_by_user_id = ?
            """,
            (existing_household_id, current_user_id),
        ).fetchone()[0]

        if existing_expense_count > 0:
            conn.close()
            return False, "This account already has expenses in another household. Move them manually before joining a new household."

        conn.execute(
            """
            DELETE FROM household_members
            WHERE user_id = ?
            """,
            (current_user_id,),
        )

    conn.execute(
        """
        INSERT OR IGNORE INTO household_members (household_id, user_id, role)
        VALUES (?, ?, 'member')
        """,
        (household_id, current_user_id),
    )

    conn.execute(
        """
        UPDATE household_invites
        SET status = 'accepted',
            accepted_by_user_id = ?
        WHERE id = ?
        """,
        (current_user_id, invite_id),
    )

    conn.commit()
    conn.close()
    return True, "Invite accepted."
