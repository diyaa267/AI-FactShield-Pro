from .db import get_connection

def save_report(user_id, report_type, file_name):
    conn = get_connection()
    conn.execute("INSERT INTO reports(user_id,report_type,file_name) VALUES(?,?,?)",
                 (user_id, report_type, file_name))
    conn.commit()
    conn.close()
