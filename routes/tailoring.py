"""
Tailoring Routes - Resume tailoring for specific jobs
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from models.database import get_db_context
from models.tailor_analysis import TailorAnalysis
from services.ai_service import get_ai_service
from datetime import datetime
import os

bp = Blueprint('tailoring', __name__, url_prefix='/tailor')


def resolve_skill_ids(analysis_data, all_skills):
    """Validate AI-returned skill IDs and fall back to name matching.

    The AI returns skills with both 'id' and 'name'. This function:
    1. Validates that returned IDs actually exist in the database
    2. For skills with names but invalid/missing IDs, matches by name (case-insensitive)
    """
    id_set = {skill['id'] for skill in all_skills}
    name_to_id = {skill['skill_name'].lower(): skill['id'] for skill in all_skills}

    resolved_skills = []
    for skill_rec in analysis_data.get('skills', []):
        skill_id = skill_rec.get('id')
        skill_name = skill_rec.get('name', '')

        if skill_id and skill_id in id_set:
            resolved_skills.append(skill_rec)
        elif skill_name:
            matched_id = name_to_id.get(skill_name.lower())
            if matched_id:
                skill_rec['id'] = matched_id
                resolved_skills.append(skill_rec)

    analysis_data['skills'] = resolved_skills
    return analysis_data


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

    db_analyses = TailorAnalysis.get_all_with_job_info()

    return render_template('tailor.html', jobs=jobs, db_analyses=db_analyses)


@bp.route('/run/<int:job_id>', methods=['POST'])
def run_tailor(job_id):
    """Run resume tailoring analysis for a specific job"""
    ai = get_ai_service()

    with get_db_context() as (conn, cursor):
        cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        job = cursor.fetchone()

        if not job:
            flash('Job not found', 'error')
            return redirect(url_for('tailoring.tailor_home'))

        cursor.execute("SELECT * FROM experiences ORDER BY id")
        experiences = cursor.fetchall()

        cursor.execute("SELECT * FROM bullets ORDER BY id")
        bullets = cursor.fetchall()

        cursor.execute("SELECT * FROM skills ORDER BY category, skill_name")
        skills = cursor.fetchall()

        cursor.execute("SELECT * FROM education ORDER BY id")
        education = cursor.fetchall()

    if not experiences and not bullets and not skills:
        flash('Please add resume components before tailoring', 'error')
        return redirect(url_for('resume.view_resume'))

    try:
        # Run AI analysis - returns parsed dict
        analysis_data = ai.match_job_to_resume(
            job, experiences, bullets, skills, education
        )

        raw_response = analysis_data.pop('_raw_response', '')

        # Resolve skill IDs (validate AI-returned IDs, match by name as fallback)
        analysis_data = resolve_skill_ids(analysis_data, skills)

        strategy_text = analysis_data.get('strategy', '')

        # Save to database
        analysis_id = TailorAnalysis.create(
            job_id=job_id,
            analysis_data=analysis_data,
            strategy_text=strategy_text,
            raw_response=raw_response
        )

        # Build lookup dictionaries for template
        exp_dict = {exp['id']: exp for exp in experiences}
        bullet_dict = {b['id']: b for b in bullets}
        skill_dict = {s['id']: s for s in skills}
        edu_dict = {e['id']: e for e in education}

        return render_template(
            'tailor_results.html',
            job=job,
            analysis=analysis_data,
            analysis_id=analysis_id,
            strategy_text=strategy_text,
            experiences=exp_dict,
            bullets=bullet_dict,
            skills=skill_dict,
            education=edu_dict,
            raw_response=raw_response,
        )

    except Exception as e:
        current_app.logger.error(f"Tailoring error: {e}")
        flash(f'Error during analysis: {str(e)}', 'error')
        return redirect(url_for('tailoring.tailor_home'))


@bp.route('/analysis/<int:analysis_id>')
def view_db_analysis(analysis_id):
    """View a DB-stored tailoring analysis"""
    analysis = TailorAnalysis.get_parsed(analysis_id)
    if not analysis:
        flash('Analysis not found', 'error')
        return redirect(url_for('tailoring.saved_analyses'))

    with get_db_context() as (conn, cursor):
        cursor.execute("SELECT * FROM jobs WHERE id = ?", (analysis['job_id'],))
        job = cursor.fetchone()

        cursor.execute("SELECT * FROM experiences ORDER BY id")
        experiences = cursor.fetchall()
        cursor.execute("SELECT * FROM bullets ORDER BY id")
        bullets = cursor.fetchall()
        cursor.execute("SELECT * FROM skills ORDER BY category, skill_name")
        skills = cursor.fetchall()
        cursor.execute("SELECT * FROM education ORDER BY id")
        education = cursor.fetchall()

    if not job:
        flash('Associated job not found', 'error')
        return redirect(url_for('tailoring.saved_analyses'))

    exp_dict = {exp['id']: exp for exp in experiences}
    bullet_dict = {b['id']: b for b in bullets}
    skill_dict = {s['id']: s for s in skills}
    edu_dict = {e['id']: e for e in education}

    return render_template(
        'tailor_results.html',
        job=job,
        analysis=analysis['analysis_data'],
        analysis_id=analysis_id,
        strategy_text=analysis.get('strategy_text', ''),
        experiences=exp_dict,
        bullets=bullet_dict,
        skills=skill_dict,
        education=edu_dict,
        raw_response=analysis.get('raw_response', ''),
    )


@bp.route('/analysis/<int:analysis_id>/delete', methods=['POST'])
def delete_db_analysis(analysis_id):
    """Delete a DB-stored tailoring analysis"""
    if TailorAnalysis.delete(analysis_id):
        flash('Analysis deleted successfully', 'success')
    else:
        flash('Analysis not found', 'error')
    return redirect(url_for('tailoring.saved_analyses'))


@bp.route('/saved')
def saved_analyses():
    """Show list of saved tailoring analyses (DB + legacy files)"""
    db_analyses = TailorAnalysis.get_all_with_job_info()

    # Legacy file-based analyses
    save_dir = os.path.join(current_app.root_path, 'saved_analyses')
    files = []
    if os.path.exists(save_dir):
        for filename in os.listdir(save_dir):
            if filename.endswith('.txt'):
                filepath = os.path.join(save_dir, filename)
                stat = os.stat(filepath)
                files.append({
                    'filename': filename,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })
        files.sort(key=lambda x: x['modified'], reverse=True)

    return render_template('saved_analyses.html', db_analyses=db_analyses, files=files)


# --- Legacy file-based analysis routes (kept for backward compat) ---

@bp.route('/saved/<filename>')
def view_analysis(filename):
    """View a legacy file-based tailoring analysis"""
    filename = secure_filename(filename)
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
    """Delete a legacy file-based tailoring analysis"""
    filename = secure_filename(filename)
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
    """Delete all saved tailoring analyses (files only)"""
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
