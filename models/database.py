"""
Database Connection Management and Initialization
"""
import sqlite3
from contextlib import contextmanager
from flask import g, current_app


def get_db():
    """
    Get database connection for the current request.
    Connection is stored in Flask's g object and reused within the request.
    """
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE_NAME'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row  # Access columns by name
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db


def close_db(e=None):
    """Close database connection at the end of request"""
    db = g.pop('db', None)
    if db is not None:
        db.close()


@contextmanager
def get_db_context():
    """
    Context manager for database operations.
    Ensures connection is always closed and commits/rollbacks are handled.
    
    Usage:
        with get_db_context() as (conn, cursor):
            cursor.execute("SELECT * FROM jobs")
            results = cursor.fetchall()
    """
    conn = sqlite3.connect(current_app.config['DATABASE_NAME'])
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    cursor = conn.cursor()
    
    try:
        yield conn, cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


def init_db():
    """Initialize all database tables"""
    conn = sqlite3.connect(current_app.config['DATABASE_NAME'])
    cursor = conn.cursor()
    
    # Jobs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            raw_html TEXT,
            raw_text TEXT,
            company_name TEXT,
            job_title TEXT,
            location TEXT,
            compensation TEXT,
            date_posted TEXT,
            requirements TEXT,
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Experiences table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS experiences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            job_title TEXT NOT NULL,
            alternate_titles TEXT,
            start_date TEXT,
            end_date TEXT,
            location TEXT,
            description TEXT
        )
    ''')
    
    # Bullet groups table (for linking alternate-wording bullets)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bullet_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            label TEXT
        )
    ''')

    # Bullets table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bullets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            experience_id INTEGER,
            bullet_text TEXT NOT NULL,
            template_text TEXT,
            tags TEXT,
            category TEXT,
            FOREIGN KEY (experience_id) REFERENCES experiences(id)
        )
    ''')

    # Migrate: add group columns to bullets if missing
    for col_sql in [
        'ALTER TABLE bullets ADD COLUMN group_id INTEGER REFERENCES bullet_groups(id)',
        'ALTER TABLE bullets ADD COLUMN is_group_default INTEGER DEFAULT 1',
    ]:
        try:
            cursor.execute(col_sql)
        except sqlite3.OperationalError as e:
            if 'duplicate column name' not in str(e):
                raise
    
    # Skills table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_name TEXT NOT NULL,
            category TEXT
        )
    ''')
    
    # Education table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS education (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_name TEXT NOT NULL,
            degree TEXT,
            field_of_study TEXT,
            graduation_year TEXT,
            location TEXT
        )
    ''')
    
    # Suggestions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            suggestion_type TEXT NOT NULL,
            component_id INTEGER,
            original_text TEXT,
            suggested_text TEXT,
            reasoning TEXT,
            status TEXT DEFAULT 'pending',
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Export profiles table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS export_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            header_info TEXT DEFAULT '{}',
            is_default INTEGER DEFAULT 0,
            date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Add header_info column if missing (migration for existing databases)
    cursor.execute("PRAGMA table_info(export_profiles)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'header_info' not in columns:
        cursor.execute("ALTER TABLE export_profiles ADD COLUMN header_info TEXT DEFAULT '{}'")

    # Export rules table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS export_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER NOT NULL,
            rule_type TEXT NOT NULL,
            rule_order INTEGER DEFAULT 0,
            config TEXT NOT NULL DEFAULT '{}',
            enabled INTEGER DEFAULT 1,
            FOREIGN KEY (profile_id) REFERENCES export_profiles(id)
        )
    ''')

    # Tailor analyses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tailor_analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            analysis_json TEXT NOT NULL,
            strategy_text TEXT DEFAULT '',
            raw_response TEXT DEFAULT '',
            date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        )
    ''')

    conn.commit()
    conn.close()
    print("✓ Database initialized successfully")


def init_app(app):
    """Register database functions with Flask app"""
    app.teardown_appcontext(close_db)
    
    with app.app_context():
        init_db()
