"""
Tailoring Routes - Resume tailoring for specific jobs
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from models.database import get_db_context
from models.resume import get_all_components
from models.tailor_analysis import TailorAnalysis
from services.ai_service import get_ai_service
from extensions import limiter

bp = Blueprint('tailoring', __name__, url_prefix='/tailor')


def _build_component_dicts(experiences, bullets, skills, education):
    """Return id-keyed lookup dicts for each component list (for template rendering)."""
    return (
        {exp['id']: exp for exp in experiences},
        {b['id']: b for b in bullets},
        {s['id']: s for s in skills},
        {e['id']: e for e in education},
    )


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
                resolved_skills.append({**skill_rec, 'id': matched_id})
            else:
                current_app.logger.warning(
                    "resolve_skill_ids: dropping unmatched skill %r (id=%r)", skill_name, skill_id
                )
        else:
            current_app.logger.warning(
                "resolve_skill_ids: dropping skill with no name and invalid id=%r", skill_id
            )

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
@limiter.limit("20 per hour")
def run_tailor(job_id):
    """Run resume tailoring analysis for a specific job"""
    ai = get_ai_service()

    with get_db_context() as (conn, cursor):
        cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        job = cursor.fetchone()

        if not job:
            flash('Job not found', 'error')
            return redirect(url_for('tailoring.tailor_home'))

    experiences, bullets, skills, education = get_all_components()

    if not experiences and not bullets and not skills:
        flash('Please add resume components before tailoring', 'error')
        return redirect(url_for('resume.view_resume'))

    try:
        # Run AI analysis - returns parsed dict
        analysis_data = ai.match_job_to_resume(
            job, experiences, bullets, skills, education
        )

        # Resolve skill IDs (validate AI-returned IDs, match by name as fallback)
        analysis_data = resolve_skill_ids(analysis_data, skills)

        strategy_text = analysis_data.get('strategy', '')

        # Save to database
        analysis_id = TailorAnalysis.create(
            job_id=job_id,
            analysis_data=analysis_data,
            strategy_text=strategy_text,
        )

        # Build lookup dictionaries for template
        exp_dict, bullet_dict, skill_dict, edu_dict = _build_component_dicts(
            experiences, bullets, skills, education
        )

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
        )

    except ValueError as e:
        current_app.logger.warning("Tailoring rejected due to input constraints: %s", e)
        flash(str(e), 'error')
        return redirect(url_for('tailoring.tailor_home'))
    except Exception as e:
        current_app.logger.exception("Tailoring error")
        flash('An error occurred during analysis. Please try again.', 'error')
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

    experiences, bullets, skills, education = get_all_components()

    if not job:
        flash('Associated job not found', 'error')
        return redirect(url_for('tailoring.saved_analyses'))

    exp_dict, bullet_dict, skill_dict, edu_dict = _build_component_dicts(
        experiences, bullets, skills, education
    )

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
    """Show list of saved tailoring analyses"""
    db_analyses = TailorAnalysis.get_all_with_job_info()
    return render_template('saved_analyses.html', db_analyses=db_analyses)
