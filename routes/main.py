"""
Main Routes - Homepage, dashboard, and authentication
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from urllib.parse import urlsplit
import secrets
import os

from extensions import limiter
from models.database import get_db_context

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    """Homepage/Dashboard"""
    with get_db_context() as (conn, cursor):
        # Get all counts in a single query
        cursor.execute("""
            SELECT
                (SELECT COUNT(*) FROM jobs) AS job_count,
                (SELECT COUNT(*) FROM experiences) AS exp_count,
                (SELECT COUNT(*) FROM bullets) AS bullet_count,
                (SELECT COUNT(*) FROM skills) AS skill_count,
                (SELECT COUNT(*) FROM suggestions WHERE status = 'pending') AS total_pending
        """)
        counts = cursor.fetchone()
        job_count = counts['job_count']
        exp_count = counts['exp_count']
        bullet_count = counts['bullet_count']
        skill_count = counts['skill_count']
        total_pending = counts['total_pending']

        # Get recent jobs (last 5)
        cursor.execute("""
            SELECT id, company_name, job_title, location, date_added
            FROM jobs
            ORDER BY date_added DESC
            LIMIT 5
        """)
        raw_jobs = cursor.fetchall()

        # Convert to list of dicts and format dates
        recent_jobs = []
        for job in raw_jobs:
            job_dict = dict(job)
            if job_dict.get('date_added'):
                date_str = str(job_dict['date_added'])
                job_dict['date_added'] = date_str[:10]
            recent_jobs.append(job_dict)

    # Count saved analyses
    save_dir = os.path.join(current_app.root_path, 'saved_analyses')
    saved_analyses_count = 0
    if os.path.exists(save_dir):
        saved_analyses_count = len([f for f in os.listdir(save_dir) if f.endswith('.txt')])

    return render_template(
        'index.html',
        job_count=job_count,
        exp_count=exp_count,
        bullet_count=bullet_count,
        skill_count=skill_count,
        total_pending=total_pending,
        saved_analyses_count=saved_analyses_count,
        recent_jobs=recent_jobs
    )


@bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    """Password login — only active when LOGIN_PASSWORD is configured."""
    # If auth is disabled, go straight to dashboard
    if not current_app.config.get('LOGIN_PASSWORD'):
        return redirect(url_for('main.index'))

    # Already logged in
    if session.get('authenticated'):
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        expected = current_app.config.get('LOGIN_PASSWORD') or ''
        if secrets.compare_digest(password, expected):
            session.clear()  # Prevent session fixation
            session['authenticated'] = True
            next_url = request.args.get('next', '')
            # Reject protocol-relative (//evil.com) and absolute URLs — only same-origin paths
            if not next_url.startswith('/') or urlsplit(next_url).netloc != '':
                next_url = url_for('main.index')
            return redirect(next_url)
        flash('Incorrect password.', 'error')

    return render_template('login.html')


@bp.route('/logout', methods=['POST'])
def logout():
    """Clear the authenticated session."""
    session.clear()
    return redirect(url_for('main.login'))
