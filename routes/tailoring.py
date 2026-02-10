"""
Tailoring Routes - Resume tailoring for specific jobs
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from models.database import get_db_context
from services.ai_service import get_ai_service
from datetime import datetime
import os
import re

bp = Blueprint('tailoring', __name__, url_prefix='/tailor')


def enrich_recommendations_with_component_text(recommendations, experiences, bullets):
    """
    Enrich the AI recommendations by adding actual component text next to ID references.

    This makes the saved analysis self-contained and easier to use without needing
    to cross-reference with the resume components.

    Args:
        recommendations: Raw text from Claude with ID references
        experiences: List of experience dictionaries
        bullets: List of bullet dictionaries

    Returns:
        Enriched recommendations text with component details inline
    """
    enriched = recommendations

    # Create lookup dictionaries
    exp_dict = {exp['id']: exp for exp in experiences}
    bullet_dict = {b['id']: b for b in bullets}

    # Pattern to find "Experience ID: X" followed by the rest of the entry
    exp_pattern = r'(- Experience ID: (\d+))'

    def replace_experience(match):
        full_match = match.group(1)
        exp_id = int(match.group(2))

        if exp_id in exp_dict:
            exp = exp_dict[exp_id]
            enrichment = f"{full_match}\n"
            enrichment += f"  → {exp['job_title']} at {exp['company_name']}\n"
            enrichment += f"  → {exp['start_date']} - {exp['end_date']}"
            if exp['location']:
                enrichment += f" | {exp['location']}"
            if exp['description']:
                enrichment += f"\n  → {exp['description']}"
            if exp['alternate_titles']:
                enrichment += f"\n  → Alternate Titles: {exp['alternate_titles']}"
            return enrichment
        return full_match

    enriched = re.sub(exp_pattern, replace_experience, enriched)

    # Pattern to find "Bullet ID: X" followed by the rest of the entry
    bullet_pattern = r'(- Bullet ID: (\d+))'

    def replace_bullet(match):
        full_match = match.group(1)
        bullet_id = int(match.group(2))

        if bullet_id in bullet_dict:
            bullet = bullet_dict[bullet_id]
            enrichment = f"{full_match}\n"
            enrichment += f"  → {bullet['bullet_text']}"
            if bullet['category']:
                enrichment += f"\n  → Category: {bullet['category']}"
            if bullet['tags']:
                enrichment += f" | Tags: {bullet['tags']}"
            return enrichment
        return full_match

    enriched = re.sub(bullet_pattern, replace_bullet, enriched)

    return enriched


@bp.route('/')
def tailor_home():
    """Show job selection page for tailoring"""
    with get_db_context() as (conn, cursor):
        cursor.execute("""
            SELECT id, company_name, job_title, location, date_added 
            FROM jobs 
            ORDER BY date_added DESC
        """)
        jobs = cursor.fetchall()
    
    return render_template('tailor.html', jobs=jobs)


@bp.route('/run/<int:job_id>', methods=['POST'])
def run_tailor(job_id):
    """Run resume tailoring analysis for a specific job"""
    ai = get_ai_service()
    
    with get_db_context() as (conn, cursor):
        # Get job details
        cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        job = cursor.fetchone()
        
        if not job:
            flash('Job not found', 'error')
            return redirect(url_for('tailoring.tailor_home'))
        
        # Get resume components
        cursor.execute("SELECT * FROM experiences ORDER BY id")
        experiences = cursor.fetchall()
        
        cursor.execute("SELECT * FROM bullets ORDER BY id")
        bullets = cursor.fetchall()
        
        cursor.execute("SELECT * FROM skills ORDER BY category, skill_name")
        skills = cursor.fetchall()
        
        cursor.execute("SELECT * FROM education ORDER BY id")
        education = cursor.fetchall()
    
    # Check if user has resume data
    if not experiences and not bullets and not skills:
        flash('Please add resume components before tailoring', 'error')
        return redirect(url_for('resume.view_resume'))
    
    try:
        # Run AI analysis
        recommendations = ai.match_job_to_resume(
            job, experiences, bullets, skills, education
        )

        # Enrich recommendations with actual component text
        enriched_recommendations = enrich_recommendations_with_component_text(
            recommendations, experiences, bullets
        )

        # Create lookup dictionaries for template
        exp_dict = {exp['id']: exp for exp in experiences}
        bullet_dict = {b['id']: b for b in bullets}

        return render_template(
            'tailor_results.html',
            job=job,
            recommendations=enriched_recommendations,
            experiences=exp_dict,
            bullets=bullet_dict
        )

    except Exception as e:
        current_app.logger.error(f"Tailoring error: {e}")
        flash(f'Error during analysis: {str(e)}', 'error')
        return redirect(url_for('tailoring.tailor_home'))


@bp.route('/save/<int:job_id>', methods=['POST'])
def save_tailor_recommendations(job_id):
    """Save tailoring recommendations to a file"""
    recommendations = request.form.get('recommendations', '')

    with get_db_context() as (conn, cursor):
        cursor.execute("SELECT company_name, job_title FROM jobs WHERE id = ?", (job_id,))
        job = cursor.fetchone()

        # Fetch resume components for enrichment
        cursor.execute("SELECT * FROM experiences ORDER BY id")
        experiences = cursor.fetchall()

        cursor.execute("SELECT * FROM bullets ORDER BY id")
        bullets = cursor.fetchall()

    if not job:
        flash('Job not found', 'error')
        return redirect(url_for('tailoring.tailor_home'))

    # Enrich recommendations with actual component text
    enriched_recommendations = enrich_recommendations_with_component_text(
        recommendations, experiences, bullets
    )
    
    # Create saved analyses directory if it doesn't exist
    save_dir = os.path.join(current_app.root_path, 'saved_analyses')
    os.makedirs(save_dir, exist_ok=True)
    
    # Generate filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_company = "".join(c for c in job['company_name'] if c.isalnum() or c in (' ', '-')).strip()
    safe_title = "".join(c for c in job['job_title'] if c.isalnum() or c in (' ', '-')).strip()
    filename = f"{timestamp}_{safe_company}_{safe_title}.txt"
    filepath = os.path.join(save_dir, filename)
    
    # Save to file
    try:
        with open(filepath, 'w') as f:
            f.write(f"Resume Tailoring Analysis\n")
            f.write(f"{'='*60}\n\n")
            f.write(f"Job: {job['job_title']}\n")
            f.write(f"Company: {job['company_name']}\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"{'='*60}\n\n")
            f.write(enriched_recommendations)

        flash(f'Tailoring analysis saved successfully!', 'success')
    except Exception as e:
        flash(f'Error saving analysis: {str(e)}', 'error')

    return redirect(url_for('tailoring.saved_analyses'))


@bp.route('/saved')
def saved_analyses():
    """Show list of saved tailoring analyses"""
    save_dir = os.path.join(current_app.root_path, 'saved_analyses')
    
    if not os.path.exists(save_dir):
        return render_template('saved_analyses.html', files=[])
    
    files = []
    for filename in os.listdir(save_dir):
        if filename.endswith('.txt'):
            filepath = os.path.join(save_dir, filename)
            stat = os.stat(filepath)
            files.append({
                'filename': filename,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            })
    
    # Sort by modified date, newest first
    files.sort(key=lambda x: x['modified'], reverse=True)
    
    return render_template('saved_analyses.html', files=files)


@bp.route('/saved/<filename>')
def view_analysis(filename):
    """View a saved tailoring analysis"""
    save_dir = os.path.join(current_app.root_path, 'saved_analyses')
    filepath = os.path.join(save_dir, filename)
    
    if not os.path.exists(filepath):
        flash('Analysis file not found', 'error')
        return redirect(url_for('tailoring.saved_analyses'))
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        return render_template('view_analysis.html', filename=filename, content=content)
    except Exception as e:
        flash(f'Error reading file: {str(e)}', 'error')
        return redirect(url_for('tailoring.saved_analyses'))


@bp.route('/saved/delete/<filename>', methods=['POST'])
def delete_analysis(filename):
    """Delete a saved tailoring analysis"""
    save_dir = os.path.join(current_app.root_path, 'saved_analyses')
    filepath = os.path.join(save_dir, filename)
    
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            flash('Analysis deleted successfully', 'success')
        else:
            flash('File not found', 'error')
    except Exception as e:
        flash(f'Error deleting file: {str(e)}', 'error')
    
    return redirect(url_for('tailoring.saved_analyses'))


@bp.route('/saved/delete-all', methods=['POST'])
def delete_all_analyses():
    """Delete all saved tailoring analyses"""
    save_dir = os.path.join(current_app.root_path, 'saved_analyses')
    
    if not os.path.exists(save_dir):
        flash('No analyses to delete', 'info')
        return redirect(url_for('tailoring.saved_analyses'))
    
    try:
        count = 0
        for filename in os.listdir(save_dir):
            if filename.endswith('.txt'):
                filepath = os.path.join(save_dir, filename)
                os.remove(filepath)
                count += 1
        
        flash(f'Successfully deleted {count} analysis file(s)', 'success')
    except Exception as e:
        flash(f'Error deleting files: {str(e)}', 'error')
    
    return redirect(url_for('tailoring.saved_analyses'))