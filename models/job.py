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
    
    SEARCHABLE_COLUMNS = {'company_name', 'job_title', 'location'}

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

        # Build WHERE clause
        where = ''
        params = []
        if search and filter_by != 'all' and filter_by in Job.SEARCHABLE_COLUMNS:
            where = f'WHERE {filter_by} LIKE ?'
            params = [f'%{search}%']
        elif search:
            where = 'WHERE company_name LIKE ? OR job_title LIKE ? OR location LIKE ?'
            params = [f'%{search}%', f'%{search}%', f'%{search}%']

        # Get total count
        cursor.execute(f'SELECT COUNT(*) FROM jobs {where}', params)
        total = cursor.fetchone()[0]

        # Get paginated results
        offset = (page - 1) * per_page
        cursor.execute(f'''
            SELECT id, company_name, job_title, location, compensation, date_added
            FROM jobs {where}
            ORDER BY date_added DESC
            LIMIT ? OFFSET ?
        ''', params + [per_page, offset])

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
            return cursor.rowcount > 0
    
    @staticmethod
    def exists(url):
        """Check if a job with this URL already exists"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT COUNT(*) FROM jobs WHERE url = ?', (url,))
        return cursor.fetchone()[0] > 0
