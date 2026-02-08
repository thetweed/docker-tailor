"""
Main Routes - Homepage and dashboard
"""
from flask import Blueprint, render_template
from models.database import get_db_context
import os
from flask import current_app
from datetime import datetime

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    """Homepage/Dashboard"""
    with get_db_context() as (conn, cursor):
        # Get counts
        cursor.execute("SELECT COUNT(*) FROM jobs")
        job_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM experiences")
        exp_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM bullets")
        bullet_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM skills")
        skill_count = cursor.fetchone()[0]
        
        # Get pending suggestions count
        cursor.execute("""
            SELECT COUNT(*) FROM suggestions 
            WHERE status = 'pending'
        """)
        total_pending = cursor.fetchone()[0]
        
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
            # Format date_added as just the date part
            if job_dict.get('date_added'):
                # If it's a string, extract the date part
                date_str = str(job_dict['date_added'])
                job_dict['date_added'] = date_str[:10]  # Get YYYY-MM-DD part
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