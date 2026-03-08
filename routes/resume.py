"""
Resume Routes - Resume component management (experiences, bullets, skills, education)
"""
import json
from collections import OrderedDict
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from models import Experience, Bullet, BulletGroup, Skill, Education, Suggestion
from models.database import get_db_context
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
    bullets_raw = Bullet.get_all()
    skills = Skill.get_all()
    education = Education.get_all()

    total_bullet_count = len(bullets_raw)

    # Build per-group data structures
    group_data = {}
    for bullet in bullets_raw:
        gid = bullet['group_id']
        if gid is not None:
            if gid not in group_data:
                group_data[gid] = {'default': None, 'alternates': []}
            if bullet['is_group_default']:
                group_data[gid]['default'] = bullet
            else:
                group_data[gid]['alternates'].append(bullet)

    # Build ordered display items (preserve id-DESC ordering, one entry per group)
    display_items = []
    seen_groups = set()
    for bullet in bullets_raw:
        gid = bullet['group_id']
        if gid is None:
            display_items.append({'type': 'solo', 'bullet': bullet})
        elif gid not in seen_groups:
            seen_groups.add(gid)
            gd = group_data[gid]
            # Edge case: no bullet marked as default — promote first one
            if gd['default'] is None and gd['alternates']:
                gd['default'] = gd['alternates'].pop(0)
            display_items.append({
                'type': 'group',
                'group_id': gid,
                'default': gd['default'],
                'alternates': gd['alternates'],
            })

    # Organize display_items into experience sub-groups (preserving order)
    exp_buckets = OrderedDict()
    for item in display_items:
        b = item['bullet'] if item['type'] == 'solo' else item['default']
        exp_id = b['experience_id']
        if exp_id not in exp_buckets:
            if b['company_name']:
                label = f"{b['job_title']} at {b['company_name']}"
            else:
                label = 'Standalone'
            exp_buckets[exp_id] = {'exp_id': exp_id, 'label': label, 'bullets': []}
        exp_buckets[exp_id]['bullets'].append(item)
    experience_groups = list(exp_buckets.values())

    # Group skills by category (preserving DB order: category, skill_name)
    skill_buckets = OrderedDict()
    for skill in skills:
        cat = skill['category'] or 'Uncategorized'
        if cat not in skill_buckets:
            skill_buckets[cat] = {'category': cat, 'skills': []}
        skill_buckets[cat]['skills'].append(skill)
    skill_groups = list(skill_buckets.values())

    return render_template(
        'resume.html',
        experiences=experiences,
        experience_groups=experience_groups,
        total_bullet_count=total_bullet_count,
        skills=skills,
        skill_groups=skill_groups,
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
            current_app.logger.exception("Resume import validation error")
            flash(str(e), 'error')
            return redirect(request.url)
        except Exception as e:
            current_app.logger.exception("Unexpected error processing resume upload")
            flash('An error occurred while processing the resume. Please try again.', 'error')
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


def check_experience_duplicate(company_name, job_title):
    """Check if an experience with the same company and title already exists"""
    with get_db_context() as (conn, cursor):
        cursor.execute(
            "SELECT id FROM experiences WHERE LOWER(company_name) = LOWER(?) AND LOWER(job_title) = LOWER(?)",
            (company_name, job_title)
        )
        return cursor.fetchone() is not None


def check_bullet_duplicate(bullet_text):
    """Check if a bullet with the same text already exists"""
    with get_db_context() as (conn, cursor):
        cursor.execute(
            "SELECT id FROM bullets WHERE LOWER(bullet_text) = LOWER(?)",
            (bullet_text,)
        )
        return cursor.fetchone() is not None


def check_skill_duplicate(skill_name):
    """Check if a skill with the same name already exists"""
    with get_db_context() as (conn, cursor):
        cursor.execute(
            "SELECT id FROM skills WHERE LOWER(skill_name) = LOWER(?)",
            (skill_name,)
        )
        return cursor.fetchone() is not None


def check_education_duplicate(school_name, degree, field_of_study):
    """Check if an education entry with the same details already exists"""
    with get_db_context() as (conn, cursor):
        cursor.execute(
            "SELECT id FROM education WHERE LOWER(school_name) = LOWER(?) AND LOWER(degree) = LOWER(?) AND LOWER(field_of_study) = LOWER(?)",
            (school_name, degree, field_of_study)
        )
        return cursor.fetchone() is not None


def _save_suggestions(suggestions_data, experience_map, bullet_map):
    """Save AI suggestions to the database.

    Args:
        suggestions_data: dict from AIService.get_resume_suggestions()
        experience_map: {company_name: experience_id}
        bullet_map: {bullet_text: bullet_id}

    Returns:
        int: number of suggestions saved
    """
    if not suggestions_data:
        return 0

    count = 0

    # Experience alternate titles
    for exp_sugg in suggestions_data.get('experience_suggestions', []):
        exp_id = experience_map.get(exp_sugg.get('company'))
        if exp_id and exp_sugg.get('alternate_titles'):
            for alt_title in exp_sugg['alternate_titles']:
                Suggestion.create(
                    suggestion_type=Suggestion.TYPE_EXPERIENCE_ALT_TITLES,
                    component_id=exp_id,
                    original_text=exp_sugg.get('current_title', ''),
                    suggested_text=alt_title.strip(),
                    reasoning='AI-suggested alternate title to appeal to different roles'
                )
                count += 1

    # Bullet improvements
    for bullet_sugg in suggestions_data.get('bullet_suggestions', []):
        bullet_id = bullet_map.get(bullet_sugg.get('original'))
        if bullet_id:
            Suggestion.create(
                suggestion_type=Suggestion.TYPE_BULLET_IMPROVEMENT,
                component_id=bullet_id,
                original_text=bullet_sugg.get('original', ''),
                suggested_text=bullet_sugg.get('improved', ''),
                reasoning=bullet_sugg.get('reason', '')
            )
            count += 1

    # New skills
    for skill_sugg in suggestions_data.get('skill_suggestions', []):
        Suggestion.create(
            suggestion_type=Suggestion.TYPE_NEW_SKILL,
            suggested_text=skill_sugg,
            reasoning='AI-suggested skill based on your experience'
        )
        count += 1

    # Clarifying questions
    for question in suggestions_data.get('clarifying_questions', []):
        Suggestion.create(
            suggestion_type=Suggestion.TYPE_CLARIFYING_QUESTION,
            suggested_text=question,
            reasoning='Question to help improve your profile'
        )
        count += 1

    return count


def _build_parsed_format_from_db():
    """Load all resume components from DB and convert to the format
    expected by AIService.get_resume_suggestions().

    Returns:
        tuple: (parsed_data, experience_map, bullet_map)
        - parsed_data: dict matching parse_resume() output format
        - experience_map: {company_name: experience_id}
        - bullet_map: {bullet_text: bullet_id}
    """
    experiences = Experience.get_all()
    bullets = Bullet.get_all()
    skills = Skill.get_all()
    education = Education.get_all()

    experience_map = {}
    bullet_map = {}

    parsed_experiences = []
    for exp in experiences:
        parsed_experiences.append({
            'company': exp['company_name'],
            'title': exp['job_title'],
            'start_date': exp['start_date'] or '',
            'end_date': exp['end_date'] or '',
            'location': exp['location'] or '',
            'description': exp['description'] or ''
        })
        experience_map[exp['company_name']] = exp['id']

    parsed_bullets = []
    for bullet in bullets:
        parsed_bullets.append({
            'text': bullet['bullet_text'],
            'experience_company': bullet['company_name'] or '',
            'category': bullet['category'] or '',
            'tags': bullet['tags'] or ''
        })
        bullet_map[bullet['bullet_text']] = bullet['id']

    parsed_skills = []
    for skill in skills:
        parsed_skills.append({
            'name': skill['skill_name'],
            'category': skill['category'] or ''
        })

    parsed_education = []
    for edu in education:
        parsed_education.append({
            'school': edu['school_name'],
            'degree': edu['degree'] or '',
            'field': edu['field_of_study'] or '',
            'graduation_year': edu['graduation_year'] or '',
            'location': edu['location'] or ''
        })

    parsed_data = {
        'experiences': parsed_experiences,
        'bullets': parsed_bullets,
        'skills': parsed_skills,
        'education': parsed_education
    }

    return parsed_data, experience_map, bullet_map


@bp.route('/analyze', methods=['POST'])
def analyze_resume():
    """Run AI suggestion analysis on existing resume components"""
    try:
        parsed_data, experience_map, bullet_map = _build_parsed_format_from_db()

        total = (len(parsed_data['experiences']) + len(parsed_data['bullets']) +
                 len(parsed_data['skills']) + len(parsed_data['education']))
        if total == 0:
            flash('No resume components to analyze. Add some first!', 'warning')
            return redirect(url_for('resume.view_resume'))

        # Dismiss existing pending suggestions before generating new ones
        for stype in [Suggestion.TYPE_EXPERIENCE_ALT_TITLES,
                      Suggestion.TYPE_BULLET_IMPROVEMENT,
                      Suggestion.TYPE_NEW_SKILL,
                      Suggestion.TYPE_CLARIFYING_QUESTION]:
            Suggestion.dismiss_all_by_type(stype)

        ai = get_ai_service()
        suggestions_data = ai.get_resume_suggestions(parsed_data)

        if not suggestions_data:
            flash('AI analysis completed but no suggestions were generated.', 'info')
            return redirect(url_for('resume.view_resume'))

        suggestion_count = _save_suggestions(suggestions_data, experience_map, bullet_map)

        flash(f'AI analysis complete! {suggestion_count} new suggestions generated.', 'success')
        return redirect(url_for('suggestions.view_suggestions'))

    except Exception as e:
        current_app.logger.exception("Error during AI resume analysis")
        flash('An error occurred during AI analysis. Please try again.', 'error')
        return redirect(url_for('resume.view_resume'))


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

        # Track what was added vs skipped
        stats = {
            'experiences_added': 0,
            'experiences_skipped': 0,
            'bullets_added': 0,
            'bullets_skipped': 0,
            'skills_added': 0,
            'skills_skipped': 0,
            'education_added': 0,
            'education_skipped': 0
        }

        # Save experiences (skip duplicates)
        for exp in parsed_data.get('experiences', []):
            if check_experience_duplicate(exp['company'], exp['title']):
                stats['experiences_skipped'] += 1
                # Still map for bullet relationships, but get existing ID
                with get_db_context() as (conn, cursor):
                    cursor.execute(
                        "SELECT id FROM experiences WHERE LOWER(company_name) = LOWER(?) AND LOWER(job_title) = LOWER(?)",
                        (exp['company'], exp['title'])
                    )
                    result = cursor.fetchone()
                    if result:
                        experience_map[exp['company']] = result['id']
            else:
                exp_id = Experience.create(
                    company_name=exp['company'],
                    job_title=exp['title'],
                    start_date=exp.get('start_date', ''),
                    end_date=exp.get('end_date', ''),
                    location=exp.get('location', ''),
                    description=exp.get('description', '')
                )
                experience_map[exp['company']] = exp_id
                stats['experiences_added'] += 1

        # Save bullets (skip duplicates)
        for bullet in parsed_data.get('bullets', []):
            if check_bullet_duplicate(bullet['text']):
                stats['bullets_skipped'] += 1
                # Still map for suggestions
                with get_db_context() as (conn, cursor):
                    cursor.execute(
                        "SELECT id FROM bullets WHERE LOWER(bullet_text) = LOWER(?)",
                        (bullet['text'],)
                    )
                    result = cursor.fetchone()
                    if result:
                        bullet_map[bullet['text']] = result['id']
            else:
                exp_id = experience_map.get(bullet.get('experience_company'))
                bullet_id = Bullet.create(
                    bullet_text=bullet['text'],
                    experience_id=exp_id,
                    tags=bullet.get('tags', ''),
                    category=bullet.get('category', '')
                )
                bullet_map[bullet['text']] = bullet_id
                stats['bullets_added'] += 1

        # Save skills (skip duplicates)
        for skill in parsed_data.get('skills', []):
            if check_skill_duplicate(skill['name']):
                stats['skills_skipped'] += 1
            else:
                Skill.create(
                    skill_name=skill['name'],
                    category=skill.get('category', '')
                )
                stats['skills_added'] += 1

        # Save education (skip duplicates)
        for edu in parsed_data.get('education', []):
            if check_education_duplicate(edu['school'], edu.get('degree', ''), edu.get('field', '')):
                stats['education_skipped'] += 1
            else:
                Education.create(
                    school_name=edu['school'],
                    degree=edu.get('degree', ''),
                    field_of_study=edu.get('field', ''),
                    graduation_year=edu.get('graduation_year', ''),
                    location=edu.get('location', '')
                )
                stats['education_added'] += 1

        # Save AI suggestions
        suggestion_count = _save_suggestions(suggestions_data, experience_map, bullet_map)

        # Clear session
        session.pop('parsed_resume', None)
        session.pop('resume_suggestions', None)

        # Build success message with stats
        total_added = (stats['experiences_added'] + stats['bullets_added'] +
                      stats['skills_added'] + stats['education_added'])
        total_skipped = (stats['experiences_skipped'] + stats['bullets_skipped'] +
                        stats['skills_skipped'] + stats['education_skipped'])

        success_msg = f'Resume imported! Added {total_added} new component(s)'
        if total_skipped > 0:
            success_msg += f', skipped {total_skipped} duplicate(s)'
        success_msg += f'. {suggestion_count} AI suggestions saved.'

        # Add detailed breakdown if there were skips
        if total_skipped > 0:
            details = []
            if stats['experiences_skipped'] > 0:
                details.append(f"{stats['experiences_skipped']} experience(s)")
            if stats['bullets_skipped'] > 0:
                details.append(f"{stats['bullets_skipped']} bullet(s)")
            if stats['skills_skipped'] > 0:
                details.append(f"{stats['skills_skipped']} skill(s)")
            if stats['education_skipped'] > 0:
                details.append(f"{stats['education_skipped']} education entry(s)")

            if details:
                flash(f'Skipped duplicates: {", ".join(details)}', 'info')

        flash(success_msg, 'success')
        return redirect(url_for('resume.view_resume'))

    except Exception as e:
        current_app.logger.exception("Error saving imported resume components")
        flash('An error occurred while saving the resume. Please try again.', 'error')
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
        if not Bullet.update(
            bullet_id,
            bullet_text=request.form['bullet_text'],
            template_text=request.form.get('template_text', ''),
            tags=request.form.get('tags', ''),
            category=request.form.get('category', '')
        ):
            flash('Bullet not found', 'error')
            return redirect(url_for('resume.view_resume'))

        # Handle group assignment
        group_id_str = request.form.get('group_id', '')
        is_default = bool(request.form.get('is_group_default'))
        if group_id_str == 'new':
            new_label = request.form.get('new_group_label', '').strip() or None
            group_id = BulletGroup.create(label=new_label)
            Bullet.set_group(bullet_id, group_id, True)
        elif group_id_str:
            try:
                Bullet.set_group(bullet_id, int(group_id_str), is_default)
            except (ValueError, TypeError):
                flash('Invalid group ID', 'error')
                return redirect(url_for('resume.view_resume'))
        else:
            Bullet.set_group(bullet_id, None, True)

        flash('Bullet updated successfully', 'success')
        return redirect(url_for('resume.view_resume'))

    bullet = Bullet.get_by_id(bullet_id)
    if not bullet:
        flash('Bullet not found', 'error')
        return redirect(url_for('resume.view_resume'))

    groups = BulletGroup.get_all()
    return render_template('edit_bullet.html', bullet=bullet, groups=groups)


@bp.route('/bullet/<int:bullet_id>/delete', methods=['POST'])
def delete_bullet(bullet_id):
    """Delete a bullet"""
    if Bullet.delete(bullet_id):
        flash('Bullet deleted successfully', 'success')
    else:
        flash('Bullet not found', 'error')
    return redirect(url_for('resume.view_resume') + '#bullets-section')


@bp.route('/bullet/<int:bullet_id>/set-default', methods=['POST'])
def set_bullet_default(bullet_id):
    """Set a bullet as the default for its group"""
    if Bullet.set_group_default(bullet_id):
        flash('Default variant updated', 'success')
    else:
        flash('Bullet not found or not in a group', 'error')
    return redirect(url_for('resume.view_resume') + '#bullets-section')


@bp.route('/bullet-group/<int:group_id>/delete', methods=['POST'])
def delete_bullet_group(group_id):
    """Ungroup all bullets in a group and delete the group"""
    BulletGroup.delete(group_id)
    flash('Bullets ungrouped successfully', 'success')
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

    existing_categories = sorted({s['category'] for s in Skill.get_all() if s['category']})
    return render_template('add_skill.html', categories=existing_categories)


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

    existing_categories = sorted({s['category'] for s in Skill.get_all() if s['category']})
    return render_template('edit_skill.html', skill=skill, categories=existing_categories)


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
        current_app.logger.exception("Error deleting resume section: %s", section_type)
        flash(f'An error occurred while deleting {section_type}. Please try again.', 'error')
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
            cursor.execute("DELETE FROM bullet_groups")
            cursor.execute("DELETE FROM skills")
            cursor.execute("DELETE FROM education")

        flash(
            f'Successfully deleted all resume components: {exp_count} experiences, '
            f'{bullet_count} bullets, {skill_count} skills, {edu_count} education entries',
            'success'
        )
    except Exception as e:
        current_app.logger.exception("Error deleting all resume components")
        flash('An error occurred while deleting resume components. Please try again.', 'error')

    return redirect(url_for('resume.view_resume'))


@bp.route('/skills/cleanup-preview', methods=['GET'])
def cleanup_skills_preview():
    """Generate AI suggestions for cleaning up skill categories"""
    skills = Skill.get_all()

    if not skills:
        flash('No skills to clean up', 'info')
        return redirect(url_for('resume.view_resume'))

    try:
        ai = get_ai_service()
        cleanup_suggestions = ai.cleanup_skill_categories(skills)

        # Store in session for the apply step
        session['skill_cleanup_suggestions'] = json.dumps(cleanup_suggestions)

        return render_template(
            'skill_cleanup_preview.html',
            suggestions=cleanup_suggestions,
            skills=skills
        )
    except Exception as e:
        flash(f'Error generating cleanup suggestions: {str(e)}', 'error')
        return redirect(url_for('resume.view_resume'))


@bp.route('/skills/cleanup-apply', methods=['POST'])
def cleanup_skills_apply():
    """Apply the AI-suggested category cleanup"""
    if 'skill_cleanup_suggestions' not in session:
        flash('No cleanup suggestions found. Please try again.', 'error')
        return redirect(url_for('resume.view_resume'))

    try:
        suggestions = json.loads(session['skill_cleanup_suggestions'])
        category_mappings = suggestions.get('category_mappings', [])

        updated_count = 0
        with get_db_context() as (conn, cursor):
            for mapping in category_mappings:
                old_category = mapping['old_category']
                new_category = mapping['new_category']

                # Update all skills with the old category to the new category
                cursor.execute(
                    "UPDATE skills SET category = ? WHERE category = ?",
                    (new_category, old_category)
                )
                updated_count += cursor.rowcount

        # Clear session
        session.pop('skill_cleanup_suggestions', None)

        flash(
            f'Successfully cleaned up skill categories! Updated {updated_count} skill(s).',
            'success'
        )
    except Exception as e:
        current_app.logger.exception("Error applying skill cleanup")
        flash('An error occurred while applying cleanup. Please try again.', 'error')

    return redirect(url_for('resume.view_resume') + '#skills-section')
