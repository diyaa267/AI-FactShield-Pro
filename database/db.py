"""SQLite by default; optional MySQL mode for MySQL Workbench testing."""
import os, sqlite3
from config import Config

def using_mysql():
    return os.environ.get("DB_TYPE", "sqlite").strip().lower() == "mysql"

class ConnectionAdapter:
    def __init__(self, raw): self.raw = raw
    def execute(self, sql, params=()):
        return self.raw.execute(sql.replace("?", "%s") if using_mysql() else sql, params)
    def executescript(self, script):
        if using_mysql():
            for statement in script.split(";"):
                if statement.strip(): self.raw.execute(statement)
        else: self.raw.executescript(script)
    def commit(self): self.raw.commit()
    def rollback(self): self.raw.rollback()
    def close(self): self.raw.close()
    def __getattr__(self, name): return getattr(self.raw, name)

def get_connection():
    if using_mysql():
        try: import pymysql
        except ImportError as exc: raise RuntimeError("Install PyMySQL: pip install pymysql") from exc
        return ConnectionAdapter(pymysql.connect(
            host=os.environ.get("MYSQL_HOST", "127.0.0.1"), port=int(os.environ.get("MYSQL_PORT", "3306")),
            user=os.environ.get("MYSQL_USER", "root"), password=os.environ.get("MYSQL_PASSWORD", ""),
            database=os.environ.get("MYSQL_DATABASE", "ai_factshield"), charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor, autocommit=False))
    conn = sqlite3.connect(Config.DATABASE); conn.execute("PRAGMA foreign_keys = ON"); conn.row_factory = sqlite3.Row
    return ConnectionAdapter(conn)

def init_db():
    conn = get_connection()
    if using_mysql():
        schema = """
        CREATE TABLE IF NOT EXISTS users (id INT PRIMARY KEY AUTO_INCREMENT, name VARCHAR(255) NOT NULL, email VARCHAR(255) UNIQUE NOT NULL, password_hash TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS history (id INT PRIMARY KEY AUTO_INCREMENT, user_id INT NULL, input_text LONGTEXT NOT NULL, prediction VARCHAR(20) NOT NULL, confidence DOUBLE NOT NULL, language VARCHAR(50), keywords TEXT, summary TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS feedback (id INT PRIMARY KEY AUTO_INCREMENT, user_id INT NULL, rating INT, message TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS reports (id INT PRIMARY KEY AUTO_INCREMENT, user_id INT NULL, report_type VARCHAR(100), file_name VARCHAR(255), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS contact_messages (id INT PRIMARY KEY AUTO_INCREMENT, name VARCHAR(255) NOT NULL, email VARCHAR(255) NOT NULL, subject VARCHAR(255) NOT NULL, message TEXT NOT NULL, user_id INT NULL, rating INT DEFAULT 5, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS news_articles (id INT PRIMARY KEY AUTO_INCREMENT, title VARCHAR(500) NOT NULL, description TEXT, url VARCHAR(1000), source VARCHAR(255), domain VARCHAR(255), provider VARCHAR(100), published_ist VARCHAR(40), category VARCHAR(80), city VARCHAR(100) DEFAULT 'Nadiad', fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE KEY uq_news_url (url(255)));
        CREATE TABLE IF NOT EXISTS news_verifications (id INT PRIMARY KEY AUTO_INCREMENT, claim LONGTEXT NOT NULL, city VARCHAR(100) DEFAULT 'Nadiad', verdict VARCHAR(20) NOT NULL, confidence DOUBLE, evidence_confirmed BOOLEAN DEFAULT FALSE, evidence_domains INT DEFAULT 0, explanation TEXT, best_source VARCHAR(255), best_url VARCHAR(1000), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        """
    else:
        schema = """
        CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, input_text TEXT NOT NULL, prediction TEXT NOT NULL, confidence REAL NOT NULL, language TEXT, keywords TEXT, summary TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS feedback (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, rating INTEGER, message TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS reports (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, report_type TEXT, file_name TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS contact_messages (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT NOT NULL, subject TEXT NOT NULL, message TEXT NOT NULL, user_id INTEGER, rating INTEGER DEFAULT 5, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS news_articles (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, description TEXT, url TEXT UNIQUE, source TEXT, domain TEXT, provider TEXT, published_ist TEXT, category TEXT, city TEXT DEFAULT 'Nadiad', fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS news_verifications (id INTEGER PRIMARY KEY AUTOINCREMENT, claim TEXT NOT NULL, city TEXT DEFAULT 'Nadiad', verdict TEXT NOT NULL, confidence REAL, evidence_confirmed INTEGER DEFAULT 0, evidence_domains INTEGER DEFAULT 0, explanation TEXT, best_source TEXT, best_url TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        """
    conn.executescript(schema); conn.commit(); conn.close()
