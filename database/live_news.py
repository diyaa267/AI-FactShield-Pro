from .db import get_connection, using_mysql

def save_articles(articles, city="Nadiad"):
    conn=get_connection(); saved=0
    for item in articles:
        try:
            vals=tuple(item.get(k,"") for k in ("title","description","url","source","domain","provider","published_ist","category"))+(city,)
            if using_mysql():
                conn.execute("INSERT INTO news_articles(title,description,url,source,domain,provider,published_ist,category,city) VALUES(?,?,?,?,?,?,?,?,?) ON DUPLICATE KEY UPDATE title=VALUES(title), description=VALUES(description), fetched_at=CURRENT_TIMESTAMP", vals)
            else:
                conn.execute("INSERT OR IGNORE INTO news_articles(title,description,url,source,domain,provider,published_ist,category,city) VALUES(?,?,?,?,?,?,?,?,?)", vals)
            saved+=1
        except Exception: pass
    conn.commit(); conn.close(); return saved

def save_verification(claim, city, verification):
    best=verification.get("best_evidence") or {}; conn=get_connection()
    conn.execute("INSERT INTO news_verifications(claim,city,verdict,confidence,evidence_confirmed,evidence_domains,explanation,best_source,best_url) VALUES(?,?,?,?,?,?,?,?,?)", (claim,city,verification.get("verdict","fake"),verification.get("verification_confidence",0),bool(verification.get("evidence_confirmed",verification.get("evidence_available",False))),verification.get("evidence_domains",0),verification.get("explanation",""),best.get("source",""),best.get("url",best.get("link",""))))
    conn.commit(); conn.close()

def get_verification_history(limit=50):
    conn=get_connection(); rows=conn.execute("SELECT * FROM news_verifications ORDER BY id DESC LIMIT ?",(limit,)).fetchall(); conn.close(); return rows
