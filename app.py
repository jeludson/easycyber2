from flask import Flask, render_template, request, jsonify
import sqlite3
import os
from datetime import datetime

try:
    import psycopg2  # Available in requirements for deployed environments
except Exception:
    psycopg2 = None

app = Flask(__name__)


# ----- Database helpers -----
def is_postgres():
    # Support both DATABASE_URL and Vercel/Neon style POSTGRES_URL
    return bool(os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL"))


def get_connection():
    """Return a DB connection to SQLite (local) or Postgres (when DATABASE_URL/POSTGRES_URL is set)."""
    if is_postgres():
        if psycopg2 is None:
            raise RuntimeError("psycopg2 not available but DATABASE_URL/POSTGRES_URL is set")
        dsn = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
        # Some providers use postgres:// — psycopg2 prefers postgresql://
        if dsn.startswith("postgres://"):
            dsn = dsn.replace("postgres://", "postgresql://", 1)
        return psycopg2.connect(dsn)
    # Default to SQLite file. On serverless (e.g., Vercel), use /tmp which is writable but ephemeral.
    sqlite_path = os.getenv("SQLITE_PATH") or ("/tmp/database.db" if os.getenv("VERCEL") else "database.db")
    return sqlite3.connect(sqlite_path)


def init_db():
    """Ensure the messages table exists."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        if is_postgres():
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL
                )
                """
            )
        else:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
        conn.commit()
    finally:
        conn.close()


init_db()

# ----- Page Routes -----
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/portfolio')
def portfolio():
    return render_template('portfolio.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')


# ----- API Route for Contact Form -----
@app.route('/api/contact', methods=['POST'])
def api_contact():
    try:
        data = request.get_json(force=True) or {}
        name = (data.get('name') or '').strip()
        email = (data.get('email') or '').strip()
        message = (data.get('message') or '').strip()

        if not name or not email or not message:
            return jsonify({'success': False, 'error': 'All fields are required'}), 400

        conn = get_connection()
        try:
            cur = conn.cursor()
            now = datetime.utcnow()
            if is_postgres():
                cur.execute(
                    "INSERT INTO messages (name, email, message, created_at) VALUES (%s, %s, %s, %s)",
                    (name, email, message, now)
                )
            else:
                cur.execute(
                    "INSERT INTO messages (name, email, message, created_at) VALUES (?, ?, ?, ?)",
                    (name, email, message, now.isoformat() + 'Z')
                )
            conn.commit()
        finally:
            conn.close()

        return jsonify({'success': True})
    except Exception as exc:
        # In production you might log this instead of returning details
        return jsonify({'success': False, 'error': str(exc)}), 500


if __name__ == '__main__':
    app.run(debug=True)
