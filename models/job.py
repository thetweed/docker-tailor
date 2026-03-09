"""
Job Model - Database operations for job postings
"""
from models.database import get_db_context, get_db


class Job:
    """Job posting model"""
    
    @staticmethod
    def create(url, raw_html, raw_text, company_name, job_title, 
               location, compensation, date_posted, requirements):
        """Create a new job posting"""
        with get_db_context() as (conn, cursor):
            cursor.execute('''
                INSERT INTO jobs (url, raw_html, raw_text, company_name, job_title, 
                                location, compensation, date_posted, requirements)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (url, raw_html, raw_text, company_name, job_title, 
                  location, compensation, date_posted, requirements))
            return cursor.lastrowid
    
    @staticmethod
    def get_by_id(job_id):
        """Get a single job by ID"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM jobs WHERE id = ?', (job_id,))
        return cursor.fetchone()
    
    # Maps filter_by values to pre-built WHERE clauses — column names never come from user input
    _FILTER_WHERE = {
        'company_name': 'WHERE company_name LIKE ?',
        'job_title':    'WHERE job_title LIKE ?',
        'location':     'WHERE location LIKE ?',
    }

    @staticmethod
    def get_all(search=None, filter_by='all', page=1, per_page=20):
        """
        Get jobs with optional search, filtering, and pagination.

        Args:
            search: Search term to filter by
            filter_by: Column to filter on ('all', 'company_name', 'job_title', 'location')
            page: Page number (1-indexed)
            per_page: Results per page

        Returns:
            tuple: (jobs list, total count)
        """
        db = get_db()
        cursor = db.cursor()

        # Build WHERE clause from a hardcoded mapping — no user input in SQL strings
        where = ''
        params = []
        if search and filter_by in Job._FILTER_WHERE:
            where = Job._FILTER_WHERE[filter_by]
            params = [f'%{search}%']
        elif search:
            where = 'WHERE company_name LIKE ? OR job_title LIKE ? OR location LIKE ?'
            params = [f'%{search}%', f'%{search}%', f'%{search}%']

        # Get total count
        cursor.execute('SELECT COUNT(*) FROM jobs ' + where, params)
        total = cursor.fetchone()[0]

        # Get paginated results
        offset = (page - 1) * per_page
        cursor.execute(
            'SELECT id, company_name, job_title, location, compensation, date_added '
            'FROM jobs ' + where + ' ORDER BY date_added DESC LIMIT ? OFFSET ?',
            params + [per_page, offset]
        )

        return cursor.fetchall(), total
    
    @staticmethod
    def get_recent(limit=5):
        """Get most recent jobs"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            SELECT id, company_name, job_title, location, date_added 
            FROM jobs 
            ORDER BY date_added DESC 
            LIMIT ?
        ''', (limit,))
        return cursor.fetchall()
    
    @staticmethod
    def count():
        """Get total number of jobs"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT COUNT(*) FROM jobs')
        return cursor.fetchone()[0]
    
    @staticmethod
    def delete(job_id):
        """Delete a job"""
        with get_db_context() as (conn, cursor):
            cursor.execute('DELETE FROM jobs WHERE id = ?', (job_id,))
            return cursor.rowcount
    
    @staticmethod
    def exists(url):
        """Check if a job with this URL already exists"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT 1 FROM jobs WHERE url = ? LIMIT 1', (url,))
        return cursor.fetchone() is not None
