"""
TailorAnalysis Model - Database operations for saved tailoring analyses
"""
import json
from models.database import get_db_context, get_db


class TailorAnalysis:
    """Tailor analysis model for storing structured AI analysis results"""

    @staticmethod
    def create(job_id, analysis_data, strategy_text=''):
        """Create a new tailor analysis.

        Args:
            job_id: ID of the job this analysis is for
            analysis_data: dict with structured analysis (will be JSON-serialized)
            strategy_text: human-readable strategy summary

        Returns:
            ID of the newly created analysis
        """
        analysis_json = json.dumps(analysis_data) if isinstance(analysis_data, dict) else analysis_data
        with get_db_context() as (conn, cursor):
            cursor.execute('''
                INSERT INTO tailor_analyses (job_id, analysis_json, strategy_text)
                VALUES (?, ?, ?)
            ''', (job_id, analysis_json, strategy_text))
            return cursor.lastrowid

    @staticmethod
    def get_by_id(analysis_id):
        """Get a single analysis by ID"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM tailor_analyses WHERE id = ?', (analysis_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    @staticmethod
    def get_parsed(analysis_id):
        """Get analysis with the JSON field parsed into a Python dict"""
        row = TailorAnalysis.get_by_id(analysis_id)
        if row:
            row['analysis_data'] = json.loads(row['analysis_json'])
        return row

    @staticmethod
    def get_by_job_id(job_id):
        """Get all analyses for a specific job, newest first"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            SELECT ta.*, j.company_name, j.job_title
            FROM tailor_analyses ta
            JOIN jobs j ON ta.job_id = j.id
            WHERE ta.job_id = ?
            ORDER BY ta.date_created DESC
        ''', (job_id,))
        return cursor.fetchall()

    @staticmethod
    def get_all_with_job_info():
        """Get all analyses with associated job info, newest first"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            SELECT ta.*, j.company_name, j.job_title, j.location
            FROM tailor_analyses ta
            JOIN jobs j ON ta.job_id = j.id
            ORDER BY ta.date_created DESC
        ''')
        return cursor.fetchall()

    @staticmethod
    def delete(analysis_id):
        """Delete a single analysis"""
        with get_db_context() as (conn, cursor):
            cursor.execute('DELETE FROM tailor_analyses WHERE id = ?', (analysis_id,))
            return cursor.rowcount

    @staticmethod
    def delete_by_job_id(job_id):
        """Delete all analyses for a specific job"""
        with get_db_context() as (conn, cursor):
            cursor.execute('DELETE FROM tailor_analyses WHERE job_id = ?', (job_id,))
            return cursor.rowcount

    @staticmethod
    def delete_all():
        """Delete all analyses"""
        with get_db_context() as (conn, cursor):
            cursor.execute('DELETE FROM tailor_analyses')
            return cursor.rowcount

    @staticmethod
    def get_recommended_ids(analysis_id):
        """Extract recommended component IDs from an analysis for export pre-selection.

        Returns a dict with sets of IDs:
        {
            'experience_ids': {1, 2, 3},
            'bullet_ids': {4, 5, 6},
            'skill_ids': {7, 8},
            'education_ids': {1},
            'skill_names': ['Python', 'Django'],
        }
        """
        row = TailorAnalysis.get_parsed(analysis_id)
        if not row:
            return None

        data = row['analysis_data']

        result = {
            'experience_ids': set(),
            'bullet_ids': set(),
            'skill_ids': set(),
            'education_ids': set(),
            'skill_names': [],
        }

        for exp in data.get('experiences', []):
            if 'id' in exp:
                result['experience_ids'].add(exp['id'])

        for bullet in data.get('bullets', []):
            if 'id' in bullet:
                result['bullet_ids'].add(bullet['id'])

        for skill in data.get('skills', []):
            if 'id' in skill:
                result['skill_ids'].add(skill['id'])
            if 'name' in skill:
                result['skill_names'].append(skill['name'])

        for edu in data.get('education', []):
            if 'id' in edu:
                result['education_ids'].add(edu['id'])

        return result
