"""
Suggestions Routes - AI suggestion management
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from models import Suggestion, Experience, Bullet, Skill
from services import get_ai_service

bp = Blueprint('suggestions', __name__, url_prefix='/suggestions')


@bp.route('/')
def view_suggestions():
    """View all AI suggestions"""
    suggestions_by_type = Suggestion.get_grouped_pending()
    
    dismissed_count = Suggestion.count_by_status(Suggestion.STATUS_DISMISSED)
    applied_count = Suggestion.count_by_status(Suggestion.STATUS_APPLIED)
    
    # Count total pending
    total_pending = sum(len(suggs) for suggs in suggestions_by_type.values())
    
    return render_template(
        'suggestions.html',
        suggestions=suggestions_by_type,
        dismissed_count=dismissed_count,
        applied_count=applied_count,
        total_pending=total_pending
    )


@bp.route('/<int:sugg_id>/apply', methods=['POST'])
def apply_suggestion(sugg_id):
    """Apply a suggestion"""
    suggestion = Suggestion.get_by_id(sugg_id)
    
    if not suggestion:
        flash('Suggestion not found', 'error')
        return redirect(url_for('suggestions.view_suggestions'))
    
    sugg_type = suggestion['suggestion_type']
    component_id = suggestion['component_id']
    suggested_text = suggestion['suggested_text']
    action = request.form.get('action', 'replace')
    
    # Map types to return sections
    section_map = {
        Suggestion.TYPE_EXPERIENCE_ALT_TITLES: 'titles-section',
        Suggestion.TYPE_BULLET_IMPROVEMENT: 'bullets-section',
        Suggestion.TYPE_NEW_SKILL: 'skills-section',
        Suggestion.TYPE_NEW_BULLET: 'new-bullets-section'
    }
    return_section = section_map.get(sugg_type, '')
    
    try:
        if sugg_type == Suggestion.TYPE_EXPERIENCE_ALT_TITLES:
            # Add alternate title to experience
            exp = Experience.get_by_id(component_id)
            if not exp:
                flash('The experience this suggestion was for no longer exists.', 'error')
                Suggestion.update_status(sugg_id, Suggestion.STATUS_DISMISSED)
                return redirect(url_for('suggestions.view_suggestions') + '#titles-section')
            current_titles = exp['alternate_titles'] if exp['alternate_titles'] else ''
            
            existing_titles = [t.strip() for t in current_titles.split(',') if t.strip()]
            new_title = suggested_text.strip()
            
            if new_title not in existing_titles:
                if current_titles:
                    new_titles = current_titles + ', ' + new_title
                else:
                    new_titles = new_title
                
                Experience.update(
                    component_id,
                    company_name=exp['company_name'],
                    job_title=exp['job_title'],
                    alternate_titles=new_titles,
                    start_date=exp['start_date'],
                    end_date=exp['end_date'],
                    location=exp['location'],
                    description=exp['description']
                )
        
        elif sugg_type == Suggestion.TYPE_BULLET_IMPROVEMENT:
            original = Bullet.get_by_id(component_id)
            if not original:
                flash('The bullet this suggestion was for no longer exists.', 'error')
                Suggestion.update_status(sugg_id, Suggestion.STATUS_DISMISSED)
                return redirect(url_for('suggestions.view_suggestions') + '#bullets-section')
            if action == 'replace':
                Bullet.update(
                    component_id,
                    bullet_text=suggested_text,
                    template_text=suggested_text,
                    tags=original['tags'],
                    category=original['category']
                )
                flash('Bullet replaced with improved version!', 'success')
            elif action == 'add_new':
                new_id = Bullet.create(
                    bullet_text=suggested_text,
                    template_text=suggested_text,
                    experience_id=original['experience_id'],
                    tags=original['tags'],
                    category=original['category']
                )
                if original['group_id']:
                    Bullet.set_group(new_id, original['group_id'], False)
                    flash('Added improved version as a new variant in the same group!', 'success')
                else:
                    flash('Added improved version as new bullet!', 'success')
        
        elif sugg_type == Suggestion.TYPE_NEW_SKILL:
            Skill.create(skill_name=suggested_text, category='ai-suggested')
        
        elif sugg_type == Suggestion.TYPE_NEW_BULLET:
            category = 'general'
            if 'Category:' in suggestion['reasoning']:
                parts = suggestion['reasoning'].split('Category:', 1)
                if len(parts) > 1 and parts[1].strip():
                    category = parts[1].split('\n')[0].strip()
            
            Bullet.create(
                bullet_text=suggested_text,
                template_text=suggested_text,
                tags='',
                category=category
            )
        
        # Mark as applied
        Suggestion.update_status(sugg_id, Suggestion.STATUS_APPLIED)
        
        if sugg_type != Suggestion.TYPE_BULLET_IMPROVEMENT:
            flash('Suggestion applied successfully!', 'success')
        
    except Exception as e:
        current_app.logger.exception("Error applying suggestion %s", sugg_id)
        flash('An error occurred while applying the suggestion. Please try again.', 'error')
    
    if return_section:
        return redirect(url_for('suggestions.view_suggestions') + f'#{return_section}')
    return redirect(url_for('suggestions.view_suggestions'))


@bp.route('/<int:sugg_id>/dismiss', methods=['POST'])
def dismiss_suggestion(sugg_id):
    """Dismiss a suggestion"""
    suggestion = Suggestion.get_by_id(sugg_id)
    
    section_map = {
        Suggestion.TYPE_EXPERIENCE_ALT_TITLES: 'titles-section',
        Suggestion.TYPE_BULLET_IMPROVEMENT: 'bullets-section',
        Suggestion.TYPE_NEW_SKILL: 'skills-section',
        Suggestion.TYPE_NEW_BULLET: 'new-bullets-section',
        Suggestion.TYPE_CLARIFYING_QUESTION: 'questions-section'
    }
    return_section = section_map.get(suggestion['suggestion_type'], '') if suggestion else ''
    
    Suggestion.update_status(sugg_id, Suggestion.STATUS_DISMISSED)
    flash('Suggestion dismissed', 'info')
    
    if return_section:
        return redirect(url_for('suggestions.view_suggestions') + f'#{return_section}')
    return redirect(url_for('suggestions.view_suggestions'))


@bp.route('/dismiss-all/<suggestion_type>', methods=['POST'])
def dismiss_all_suggestions(suggestion_type):
    """Dismiss all suggestions of a specific type"""
    count = Suggestion.dismiss_all_by_type(suggestion_type)
    
    type_names = {
        Suggestion.TYPE_CLARIFYING_QUESTION: 'clarifying questions',
        Suggestion.TYPE_EXPERIENCE_ALT_TITLES: 'title suggestions',
        Suggestion.TYPE_BULLET_IMPROVEMENT: 'bullet improvements',
        Suggestion.TYPE_NEW_SKILL: 'skill suggestions',
        Suggestion.TYPE_NEW_BULLET: 'bullet suggestions'
    }
    
    friendly_name = type_names.get(suggestion_type, 'suggestions')
    flash(f'Dismissed all {count} {friendly_name}', 'info')
    
    section_map = {
        Suggestion.TYPE_EXPERIENCE_ALT_TITLES: 'titles-section',
        Suggestion.TYPE_BULLET_IMPROVEMENT: 'bullets-section',
        Suggestion.TYPE_NEW_SKILL: 'skills-section',
        Suggestion.TYPE_NEW_BULLET: 'new-bullets-section',
        Suggestion.TYPE_CLARIFYING_QUESTION: 'questions-section'
    }
    
    return_section = section_map.get(suggestion_type, '')
    if return_section:
        return redirect(url_for('suggestions.view_suggestions') + f'#{return_section}')
    return redirect(url_for('suggestions.view_suggestions'))


@bp.route('/<int:sugg_id>/answer', methods=['POST'])
def answer_question(sugg_id):
    """Answer a clarifying question and generate actionable suggestions"""
    answer = request.form.get('answer', '').strip()
    
    if not answer:
        flash('Please provide an answer', 'error')
        return redirect(url_for('suggestions.view_suggestions') + '#questions-section')
    
    question_sugg = Suggestion.get_by_id(sugg_id)
    
    if not question_sugg:
        flash('Question not found', 'error')
        return redirect(url_for('suggestions.view_suggestions'))
    
    question_text = question_sugg['suggested_text']
    
    created_bullets = 0
    created_skills = 0
    
    try:
        ai = get_ai_service()
        analysis = ai.analyze_question_answer(question_text, answer)
        
        # Create suggestions for each component
        for skill in analysis.get('skills_to_add', []):
            Suggestion.create(
                suggestion_type=Suggestion.TYPE_NEW_SKILL,
                suggested_text=skill['name'],
                reasoning=f"From answer to: {question_text}. Category: {skill.get('category', 'general')}"
            )
            created_skills += 1
        
        for bullet in analysis.get('bullets_to_add', []):
            Suggestion.create(
                suggestion_type=Suggestion.TYPE_NEW_BULLET,
                suggested_text=bullet['text'],
                reasoning=f"From answer to: {question_text}. Category: {bullet.get('category', 'general')}"
            )
            created_bullets += 1
        
        # Mark question as applied and store the answer
        Suggestion.update_status(
            sugg_id,
            Suggestion.STATUS_APPLIED,
            reasoning=f"Answer: {answer}\n\nGenerated suggestions: {analysis.get('notes', '')}"
        )
        
        new_suggestions = created_skills + created_bullets
        if new_suggestions > 0:
            flash(
                f'Answer saved! Created {new_suggestions} new suggestions based on your answer.',
                'success'
            )
        else:
            flash('Answer saved! No new components suggested from this answer.', 'info')
    
    except Exception as e:
        # Still save the answer even if AI analysis fails
        Suggestion.update_status(
            sugg_id,
            Suggestion.STATUS_APPLIED,
            reasoning=f"Answer: {answer}"
        )
        flash('Answer saved! (AI analysis unavailable)', 'warning')
    
    # Redirect to newly created suggestions
    if created_bullets > 0:
        return redirect(url_for('suggestions.view_suggestions') + '#new-bullets-section')
    elif created_skills > 0:
        return redirect(url_for('suggestions.view_suggestions') + '#skills-section')
    else:
        return redirect(url_for('suggestions.view_suggestions') + '#questions-section')
