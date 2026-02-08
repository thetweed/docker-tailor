"""
Suggestion Model - Database operations for AI suggestions
"""
from models.database import get_db_context, get_db


class Suggestion:
    """AI suggestion model"""
    
    # Suggestion types
    TYPE_EXPERIENCE_ALT_TITLES = 'experience_alternate_titles'
    TYPE_BULLET_IMPROVEMENT = 'bullet_improvement'
    TYPE_NEW_SKILL = 'new_skill'
    TYPE_NEW_BULLET = 'new_bullet'
    TYPE_CLARIFYING_QUESTION = 'clarifying_question'
    
    # Statuses
    STATUS_PENDING = 'pending'
    STATUS_APPLIED = 'applied'
    STATUS_DISMISSED = 'dismissed'
    
    @staticmethod
    def create(suggestion_type, suggested_text, reasoning='', 
               component_id=None, original_text=''):
        """Create a new suggestion"""
        with get_db_context() as (conn, cursor):
            cursor.execute('''
                INSERT INTO suggestions (suggestion_type, component_id, original_text, 
                                       suggested_text, reasoning, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (suggestion_type, component_id, original_text, 
                  suggested_text, reasoning, Suggestion.STATUS_PENDING))
            return cursor.lastrowid
    
    @staticmethod
    def get_by_id(sugg_id):
        """Get a single suggestion by ID"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM suggestions WHERE id = ?', (sugg_id,))
        return cursor.fetchone()
    
    @staticmethod
    def get_pending():
        """Get all pending suggestions with joined component info"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            SELECT s.*, 
                   e.company_name, e.job_title as exp_title,
                   b.bullet_text
            FROM suggestions s
            LEFT JOIN experiences e ON s.component_id = e.id 
                AND s.suggestion_type = ?
            LEFT JOIN bullets b ON s.component_id = b.id 
                AND s.suggestion_type = ?
            WHERE s.status = ?
            ORDER BY s.date_added DESC
        ''', (Suggestion.TYPE_EXPERIENCE_ALT_TITLES, 
              Suggestion.TYPE_BULLET_IMPROVEMENT,
              Suggestion.STATUS_PENDING))
        return cursor.fetchall()
    
    @staticmethod
    def get_by_type(suggestion_type, status=STATUS_PENDING):
        """Get suggestions by type and status"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            SELECT * FROM suggestions 
            WHERE suggestion_type = ? AND status = ?
            ORDER BY date_added DESC
        ''', (suggestion_type, status))
        return cursor.fetchall()
    
    @staticmethod
    def count_by_status(status):
        """Count suggestions by status"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT COUNT(*) FROM suggestions WHERE status = ?', (status,))
        return cursor.fetchone()[0]
    
    @staticmethod
    def update_status(sugg_id, status, reasoning=None):
        """Update suggestion status and optionally update reasoning"""
        with get_db_context() as (conn, cursor):
            if reasoning:
                cursor.execute('''
                    UPDATE suggestions 
                    SET status = ?, reasoning = ?
                    WHERE id = ?
                ''', (status, reasoning, sugg_id))
            else:
                cursor.execute('''
                    UPDATE suggestions 
                    SET status = ?
                    WHERE id = ?
                ''', (status, sugg_id))
            return cursor.rowcount > 0
    
    @staticmethod
    def dismiss_all_by_type(suggestion_type):
        """Dismiss all pending suggestions of a specific type"""
        with get_db_context() as (conn, cursor):
            cursor.execute('''
                UPDATE suggestions 
                SET status = ? 
                WHERE suggestion_type = ? AND status = ?
            ''', (Suggestion.STATUS_DISMISSED, suggestion_type, Suggestion.STATUS_PENDING))
            return cursor.rowcount
    
    @staticmethod
    def get_grouped_pending():
        """
        Get pending suggestions grouped by type.
        Returns a dictionary with type as key and list of suggestions as value.
        """
        pending = Suggestion.get_pending()
        
        grouped = {
            Suggestion.TYPE_EXPERIENCE_ALT_TITLES: [],
            Suggestion.TYPE_BULLET_IMPROVEMENT: [],
            Suggestion.TYPE_NEW_SKILL: [],
            Suggestion.TYPE_NEW_BULLET: [],
            Suggestion.TYPE_CLARIFYING_QUESTION: []
        }
        
        for sugg in pending:
            sugg_type = sugg['suggestion_type']
            if sugg_type in grouped:
                grouped[sugg_type].append(sugg)
        
        return grouped
