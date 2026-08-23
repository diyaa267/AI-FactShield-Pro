from .db import get_connection

def add_contact(name, email, subject, message, user_id=None, rating=5):
    conn = get_connection()
    conn.execute(
        "INSERT INTO contact_messages(name,email,subject,message,user_id,rating) VALUES(?,?,?,?,?,?)",
        (name, email, subject, message, user_id, rating),
    )
    conn.commit()
    conn.close()
