from werkzeug.security import generate_password_hash, check_password_hash
from .db import get_connection

def create_user(name, email, password):
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO users(name,email,password_hash) VALUES(?,?,?)",
            (name.strip(), email.strip().lower(), generate_password_hash(password))
        )
        conn.commit()
        return cur.lastrowid
    except Exception:
        return None
    finally:
        conn.close()

def get_user_by_email(email):
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE email=?", (email.strip().lower(),)).fetchone()
    conn.close()
    return row

def get_user(user_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    return row

def verify_user(email, password):
    user = get_user_by_email(email)
    if user and check_password_hash(user["password_hash"], password):
        return user
    return None
