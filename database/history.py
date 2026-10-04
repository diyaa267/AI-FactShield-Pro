from .db import get_connection

def add_history(user_id, input_text, prediction, confidence, language, keywords, summary):
    conn = get_connection()
    conn.execute("""
        INSERT INTO history(user_id,input_text,prediction,confidence,language,keywords,summary)
        VALUES(?,?,?,?,?,?,?)
    """, (user_id, input_text, prediction, confidence, language, keywords, summary))
    conn.commit()
    conn.close()

def get_history(user_id=None, limit=100):
    conn = get_connection()
    if user_id:
        rows = conn.execute(
            "SELECT * FROM history WHERE user_id=? ORDER BY id DESC LIMIT ?",
            (user_id, limit)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM history ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    conn.close()
    return rows

def stats(user_id=None):
    conn = get_connection()
    where = "WHERE user_id=?" if user_id else ""
    params = (user_id,) if user_id else ()
    total = conn.execute(f"SELECT COUNT(*) c FROM history {where}", params).fetchone()["c"]
    fake = conn.execute(f"SELECT COUNT(*) c FROM history {where} AND prediction='fake'" if where else
                        "SELECT COUNT(*) c FROM history WHERE prediction='fake'", params).fetchone()["c"]
    real = conn.execute(f"SELECT COUNT(*) c FROM history {where} AND prediction='real'" if where else
                        "SELECT COUNT(*) c FROM history WHERE prediction='real'", params).fetchone()["c"]
    avg = conn.execute(f"SELECT AVG(confidence) c FROM history {where}", params).fetchone()["c"] or 0
    conn.close()
    return {"total": total, "fake": fake, "real": real, "avg_confidence": round(avg, 2)}
