from utils.db import get_connection


def _get(row, key, index=None, default=None):
    if row is None:
        return default

    try:
        return row[key]
    except Exception:
        pass

    if index is not None:
        try:
            return row[index]
        except Exception:
            pass

    return default


def fetch_household_members(household_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            hm.user_id,
            hm.role,
            hm.joined_at,
            u.full_name,
            u.email
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


def remove_household_member(household_id, acting_user_id, target_user_id):
    conn = get_connection()
    cursor = conn.cursor()

    # Acting user must be owner of this household
    cursor.execute(
        """
        SELECT role
        FROM household_members
        WHERE household_id = ?
          AND user_id = ?
        LIMIT 1
        """,
        (household_id, acting_user_id),
    )
    acting_membership = cursor.fetchone()

    acting_role = _get(acting_membership, "role", 0)
    if acting_role != "owner":
        conn.close()
        return False, "Only the household owner can remove members."

    if acting_user_id == target_user_id:
        conn.close()
        return False, "You cannot remove yourself."

    # Target must be in the same household
    cursor.execute(
        """
        SELECT role
        FROM household_members
        WHERE household_id = ?
          AND user_id = ?
        LIMIT 1
        """,
        (household_id, target_user_id),
    )
    target_membership = cursor.fetchone()

    if not target_membership:
        conn.close()
        return False, "That user is not in your household."

    target_role = _get(target_membership, "role", 0)
    if target_role == "owner":
        conn.close()
        return False, "You cannot remove another owner."

    cursor.execute(
        """
        DELETE FROM household_members
        WHERE household_id = ?
          AND user_id = ?
        """,
        (household_id, target_user_id),
    )

    conn.commit()
    conn.close()
    return True, "User removed from household."