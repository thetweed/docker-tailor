"""
Resume Routes - Resume component management (experiences, bullets, skills, education)
"""
import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import Experience, Bullet, Skill, Education, Suggestion
from services import get_ai_service
from utils import save_uploaded_file, extract_text_from_file, cleanup_file

bp = Blueprint('resume', __name__, url_prefix='/resume')


# ============================================================================
# MAIN RESUME VIEW
# ============================================================================

@bp.route('/')
def view_resume():
    """View all resume components"""
    experiences = Experience.get_all()
    bullets = Bullet.get_all()
    skills = Skill.get_all()
    education = Education.get_all()
    
    return render_template(
        'resume.html',
        experiences=experiences,
        bullets=bullets,
        skills=skills,
        education=education
    )


# ============================================================================
# RESUME IMPORT
# ============================================================================

@bp.route('/import', methods=['GET', 'POST'])
def import_resume():
    """Import resume from file"""
    if request.method == 'POST':
        if 'resume_file' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(request.url)
        
        file = request.files['resume_file']
        
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        try:
            # Save file
            filepath = save_uploaded_file(file)
            flash(f'File uploaded: {file.filename}', 'info')
            
            # Extract text
            flash('Extracting text from file...', 'info')
            resume_text = extract_text_from_file(filepath)
            flash(f'Extracted {len(resume_text)} characters', 'info')
            
            # Parse with AI
            flash('Analyzing resume with Claude AI...', 'info')
            ai = get_ai_service()
            parsed_data = ai.parse_resume(resume_text)
            
            if not parsed_data:
                flash('Could not parse resume. Please try again.', 'error')
                cleanup_file(filepath)
                return redirect(request.url)
            
            flash('Resume parsed successfully!', 'success')
            
            # Get AI suggestions
            flash('Getting AI suggestions...', 'info')
            suggestions = ai.get_resume_suggestions(parsed_data)
            
            if suggestions:
                flash('AI suggestions generated!', 'success')
            else:
                flash('Could not generate suggestions, but resume was parsed.', 'warning')
            
            # Store in session for review page
            session['parsed_resume'] = json.dumps(parsed_data)
            session['resume_suggestions'] = json.dumps(suggestions) if suggestions else None
            
            # Clean up uploaded file
            cleanup_file(filepath)
            
            return redirect(url_for('resume.review_import'))
            
        except ValueError as e:
            flash(str(e), 'error')
            return redirect(request.url)
        except Exception as e:
            flash(f'Error processing resume: {str(e)}', 'error')
            return redirect(request.url)
    
    return render_template('import_resume.html')


@bp.route('/import/review')
def review_import():
    """Review parsed resume before saving"""
    if 'parsed_resume' not in session:
        flash('No resume data found. Please upload a resume first.', 'error')
        return redirect(url_for('resume.import_resume'))
    
    parsed_data = json.loads(session['parsed_resume'])
    suggestions = (
        json.loads(session['resume_suggestions']) 
        if session.get('resume_suggestions') 
        else None
    )
    
    return render_template(
        'review_resume_import.html',
        data=parsed_data,
        suggestions=suggestions
    )


@bp.route('/import/save', methods=['POST'])
def save_import():
    """Save the reviewed resume components to database"""
    if 'parsed_resume' not in session:
        flash('No resume data found', 'error')
        return redirect(url_for('resume.import_resume'))
    
    parsed_data = json.loads(session['parsed_resume'])
    suggestions_data = (
        json.loads(session['resume_suggestions'])
        if session.get('resume_suggestions')
        else None
    )
    
    try:
        experience_map = {}
        bullet_map = {}
        
        # Save experiences
        for exp in parsed_data.get('experiences', []):
            exp_id = Experience.create(
                company_name=exp['company'],
                job_title=exp['title'],
                start_date=exp.get('start_date', ''),
                end_date=exp.get('end_date', ''),
                location=exp.get('location', ''),
                description=exp.get('description', '')
            )
            experience_map[exp['company']] = exp_id
        
        # Save bullets
        for bullet in parsed_data.get('bullets', []):
            exp_id = experience_map.get(bullet.get('experience_company'))
            bullet_id = Bullet.create(
                bullet_text=bullet['text'],
                experience_id=exp_id,
                tags=bullet.get('tags', ''),
                category=bullet.get('category', '')
            )
            bullet_map[bullet['text']] = bullet_id
        
        # Save skills
        for skill in parsed_data.get('skills', []):
            Skill.create(
                skill_name=skill['name'],
                category=skill.get('category', '')
            )
        
        # Save education
        for edu in parsed_data.get('education', []):
            Education.create(
                school_name=edu['school'],
                degree=edu.get('degree', ''),
                field_of_study=edu.get('field', ''),
                graduation_year=edu.get('graduation_year', ''),
                location=edu.get('location', '')
            )
        
        # Save AI suggestions
        suggestion_count = 0
        if suggestions_data:
            # Experience alternate titles
            for exp_sugg in suggestions_data.get('experience_suggestions', []):
                exp_id = experience_map.get(exp_sugg['company'])
                if exp_id and exp_sugg.get('alternate_titles'):
                    for alt_title in exp_sugg['alternate_titles']:
                        Suggestion.create(
                            suggestion_type=Suggestion.TYPE_EXPERIENCE_ALT_TITLES,
                            component_id=exp_id,
                            original_text=exp_sugg['current_title'],
                            suggested_text=alt_title.strip(),
                            reasoning='AI-suggested alternate title to appeal to different roles'
                        )
                        suggestion_count += 1
            
            # Bullet improvements
            for bullet_sugg in suggestions_data.get('bullet_suggestions', []):
                bullet_id = bullet_map.get(bullet_sugg['original'])
                if bullet_id:
                    Suggestion.create(
                        suggestion_type=Suggestion.TYPE_BULLET_IMPROVEMENT,
                        component_id=bullet_id,
                        original_text=bullet_sugg['original'],
                        suggested_text=bullet_sugg['improved'],
                        reasoning=bullet_sugg['reason']
                    )
                    suggestion_count += 1
            
            # New skills
            for skill_sugg in suggestions_data.get('skill_suggestions', []):
                Suggestion.create(
                    suggestion_type=Suggestion.TYPE_NEW_SKILL,
                    suggested_text=skill_sugg,
                    reasoning='AI-suggested skill based on your experience'
                )
                suggestion_count += 1
            
            # Clarifying questions
            for question in suggestions_data.get('clarifying_questions', []):
                Suggestion.create(
                    suggestion_type=Suggestion.TYPE_CLARIFYING_QUESTION,
                    suggested_text=question,
                    reasoning='Question to help improve your profile'
                )
                suggestion_count += 1
        
        # Clear session
        session.pop('parsed_resume', None)
        session.pop('resume_suggestions', None)
        
        flash(
            f'Resume imported successfully! {suggestion_count} AI suggestions saved.',
            'success'
        )
        return redirect(url_for('resume.view_resume'))
        
    except Exception as e:
        flash(f'Error saving resume: {str(e)}', 'error')
        return redirect(url_for('resume.review_import'))


# ============================================================================
# EXPERIENCE CRUD
# ============================================================================

@bp.route('/experience/add', methods=['GET', 'POST'])
def add_experience():
    """Add a new experience"""
    if request.method == 'POST':
        Experience.create(
            company_name=request.form['company'],
            job_title=request.form['title'],
            alternate_titles=request.form.get('alt_titles', ''),
            start_date=request.form.get('start_date', ''),
            end_date=request.form.get('end_date', ''),
            location=request.form.get('location', ''),
            description=request.form.get('description', '')
        )
        flash('Experience added successfully', 'success')
        return redirect(url_for('resume.view_resume'))
    
    return render_template('add_experience.html')


@bp.route('/experience/<int:exp_id>/edit', methods=['GET', 'POST'])
def edit_experience(exp_id):
    """Edit an experience"""
    if request.method == 'POST':
        if Experience.update(
            exp_id,
            company_name=request.form['company'],
            job_title=request.form['title'],
            alternate_titles=request.form.get('alt_titles', ''),
            start_date=request.form.get('start_date', ''),
            end_date=request.form.get('end_date', ''),
            location=request.form.get('location', ''),
            description=request.form.get('description', '')
        ):
            flash('Experience updated successfully', 'success')
        else:
            flash('Experience not found', 'error')
        return redirect(url_for('resume.view_resume'))
    
    experience = Experience.get_by_id(exp_id)
    if not experience:
        flash('Experience not found', 'error')
        return redirect(url_for('resume.view_resume'))
    
    return render_template('edit_experience.html', exp=experience)


@bp.route('/experience/<int:exp_id>/delete', methods=['POST'])
def delete_experience(exp_id):
    """Delete an experience"""
    if Experience.delete(exp_id):
        flash('Experience deleted successfully', 'success')
    else:
        flash('Experience not found', 'error')
    return redirect(url_for('resume.view_resume') + '#experiences-section')


# ============================================================================
# BULLET CRUD
# ============================================================================

@bp.route('/bullet/add', methods=['GET', 'POST'])
def add_bullet():
    """Add a new bullet"""
    if request.method == 'POST':
        exp_id = request.form.get('experience_id')
        if exp_id == '':
            exp_id = None
        
        Bullet.create(
            bullet_text=request.form['bullet_text'],
            template_text=request.form.get('template_text'),
            experience_id=exp_id,
            tags=request.form.get('tags', ''),
            category=request.form.get('category', '')
        )
        flash('Bullet added successfully', 'success')
        return redirect(url_for('resume.view_resume'))
    
    experiences = Experience.get_all()
    return render_template('add_bullet.html', experiences=experiences)


@bp.route('/bullet/<int:bullet_id>/edit', methods=['GET', 'POST'])
def edit_bullet(bullet_id):
    """Edit a bullet"""
    if request.method == 'POST':
        if Bullet.update(
            bullet_id,
            bullet_text=request.form['bullet_text'],
            template_text=request.form.get('template_text', ''),
            tags=request.form.get('tags', ''),
            category=request.form.get('category', '')
        ):
            flash('Bullet updated successfully', 'success')
        else:
            flash('Bullet not found', 'error')
        return redirect(url_for('resume.view_resume'))
    
    bullet = Bullet.get_by_id(bullet_id)
    if not bullet:
        flash('Bullet not found', 'error')
        return redirect(url_for('resume.view_resume'))
    
    return render_template('edit_bullet.html', bullet=bullet)


@bp.route('/bullet/<int:bullet_id>/delete', methods=['POST'])
def delete_bullet(bullet_id):
    """Delete a bullet"""
    if Bullet.delete(bullet_id):
        flash('Bullet deleted successfully', 'success')
    else:
        flash('Bullet not found', 'error')
    return redirect(url_for('resume.view_resume') + '#bullets-section')


# ============================================================================
# SKILL CRUD
# ============================================================================

@bp.route('/skill/add', methods=['GET', 'POST'])
def add_skill():
    """Add a new skill"""
    if request.method == 'POST':
        Skill.create(
            skill_name=request.form['skill_name'],
            category=request.form.get('category', '')
        )
        flash('Skill added successfully', 'success')
        return redirect(url_for('resume.view_resume'))
    
    return render_template('add_skill.html')


@bp.route('/skill/<int:skill_id>/edit', methods=['GET', 'POST'])
def edit_skill(skill_id):
    """Edit a skill"""
    if request.method == 'POST':
        if Skill.update(
            skill_id,
            skill_name=request.form['skill_name'],
            category=request.form.get('category', '')
        ):
            flash('Skill updated successfully', 'success')
        else:
            flash('Skill not found', 'error')
        return redirect(url_for('resume.view_resume'))
    
    skill = Skill.get_by_id(skill_id)
    if not skill:
        flash('Skill not found', 'error')
        return redirect(url_for('resume.view_resume'))
    
    return render_template('edit_skill.html', skill=skill)


@bp.route('/skill/<int:skill_id>/delete', methods=['POST'])
def delete_skill(skill_id):
    """Delete a skill"""
    if Skill.delete(skill_id):
        flash('Skill deleted successfully', 'success')
    else:
        flash('Skill not found', 'error')
    return redirect(url_for('resume.view_resume') + '#skills-section')


# ============================================================================
# EDUCATION CRUD
# ============================================================================

@bp.route('/education/add', methods=['GET', 'POST'])
def add_education():
    """Add a new education entry"""
    if request.method == 'POST':
        Education.create(
            school_name=request.form['school'],
            degree=request.form.get('degree', ''),
            field_of_study=request.form.get('field', ''),
            graduation_year=request.form.get('grad_year', ''),
            location=request.form.get('location', '')
        )
        flash('Education added successfully', 'success')
        return redirect(url_for('resume.view_resume'))
    
    return render_template('add_education.html')


@bp.route('/education/<int:edu_id>/edit', methods=['GET', 'POST'])
def edit_education(edu_id):
    """Edit an education entry"""
    if request.method == 'POST':
        if Education.update(
            edu_id,
            school_name=request.form['school'],
            degree=request.form.get('degree', ''),
            field_of_study=request.form.get('field', ''),
            graduation_year=request.form.get('grad_year', ''),
            location=request.form.get('location', '')
        ):
            flash('Education updated successfully', 'success')
        else:
            flash('Education not found', 'error')
        return redirect(url_for('resume.view_resume'))
    
    education = Education.get_by_id(edu_id)
    if not education:
        flash('Education not found', 'error')
        return redirect(url_for('resume.view_resume'))
    
    return render_template('edit_education.html', edu=education)


@bp.route('/education/<int:edu_id>/delete', methods=['POST'])
def delete_education(edu_id):
    """Delete an education entry"""
    if Education.delete(edu_id):
        flash('Education deleted successfully', 'success')
    else:
        flash('Education not found', 'error')
    return redirect(url_for('resume.view_resume') + '#education-section')


# ============================================================================
# BULK DELETE OPERATIONS
# ============================================================================

@bp.route('/delete-section/<section_type>', methods=['POST'])
def delete_section(section_type):
    """Delete all components in a specific section"""
    section_map = {
        'experiences': (Experience, 'experiences-section'),
        'bullets': (Bullet, 'bullets-section'),
        'skills': (Skill, 'skills-section'),
        'education': (Education, 'education-section')
    }
    
    if section_type not in section_map:
        flash('Invalid section type', 'error')
        return redirect(url_for('resume.view_resume'))
    
    model_class, anchor = section_map[section_type]
    
    try:
        count = model_class.delete_all()
        flash(f'Deleted all {count} {section_type}', 'warning')
        return redirect(url_for('resume.view_resume') + f'#{anchor}')
    except Exception as e:
        flash(f'Error deleting {section_type}: {str(e)}', 'error')
        return redirect(url_for('resume.view_resume'))

@bp.route('/delete-all', methods=['POST'])
def delete_all_components():
    """Delete all resume components"""
    confirm_text = request.form.get('confirm_delete_all', '')
    
    if confirm_text != 'DELETE_EVERYTHING':
        flash('Confirmation text did not match. Nothing was deleted.', 'error')
        return redirect(url_for('resume.view_resume'))
    
    from models.database import get_db_context
    
    try:
        with get_db_context() as (conn, cursor):
            # Count items before deletion
            cursor.execute("SELECT COUNT(*) FROM experiences")
            exp_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM bullets")
            bullet_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM skills")
            skill_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM education")
            edu_count = cursor.fetchone()[0]
            
            total = exp_count + bullet_count + skill_count + edu_count
            
            # Delete everything
            cursor.execute("DELETE FROM experiences")
            cursor.execute("DELETE FROM bullets")
            cursor.execute("DELETE FROM skills")
            cursor.execute("DELETE FROM education")
            
            conn.commit()
        
        flash(
            f'Successfully deleted all resume components: {exp_count} experiences, '
            f'{bullet_count} bullets, {skill_count} skills, {edu_count} education entries',
            'success'
        )
    except Exception as e:
        flash(f'Error deleting components: {str(e)}', 'error')
    
    return redirect(url_for('resume.view_resume'))