from .db import get_connection

def add_feedback(user_id, rating, message):
    conn = get_connection()
    conn.execute("INSERT INTO feedback(user_id,rating,message) VALUES(?,?,?)",
                 (user_id, rating, message))
    conn.commit()
    conn.close()
