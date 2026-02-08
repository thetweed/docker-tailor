"""
Resume Models - Database operations for resume components
"""
from models.database import get_db_context, get_db


class Experience:
    """Work experience model"""
    
    @staticmethod
    def create(company_name, job_title, alternate_titles='', start_date='', 
               end_date='', location='', description=''):
        """Create a new experience"""
        with get_db_context() as (conn, cursor):
            cursor.execute('''
                INSERT INTO experiences (company_name, job_title, alternate_titles, 
                                       start_date, end_date, location, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (company_name, job_title, alternate_titles, start_date, 
                  end_date, location, description))
            return cursor.lastrowid
    
    @staticmethod
    def get_by_id(exp_id):
        """Get a single experience by ID"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM experiences WHERE id = ?', (exp_id,))
        return cursor.fetchone()
    
    @staticmethod
    def get_all():
        """Get all experiences"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM experiences ORDER BY id DESC')
        return cursor.fetchall()
    
    @staticmethod
    def update(exp_id, company_name, job_title, alternate_titles, 
               start_date, end_date, location, description):
        """Update an experience"""
        with get_db_context() as (conn, cursor):
            cursor.execute('''
                UPDATE experiences 
                SET company_name = ?, job_title = ?, alternate_titles = ?, 
                    start_date = ?, end_date = ?, location = ?, description = ?
                WHERE id = ?
            ''', (company_name, job_title, alternate_titles, start_date, 
                  end_date, location, description, exp_id))
            return cursor.rowcount > 0
    
    @staticmethod
    def delete(exp_id):
        """Delete an experience"""
        with get_db_context() as (conn, cursor):
            cursor.execute('DELETE FROM experiences WHERE id = ?', (exp_id,))
            return cursor.rowcount > 0
    
    @staticmethod
    def count():
        """Get total number of experiences"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT COUNT(*) FROM experiences')
        return cursor.fetchone()[0]
    
    @staticmethod
    def delete_all():
        """Delete all experiences"""
        with get_db_context() as (conn, cursor):
            cursor.execute('DELETE FROM experiences')
            return cursor.rowcount


class Bullet:
    """Bullet point model"""
    
    @staticmethod
    def create(bullet_text, template_text=None, experience_id=None, 
               tags='', category=''):
        """Create a new bullet"""
        if template_text is None:
            template_text = bullet_text
            
        with get_db_context() as (conn, cursor):
            cursor.execute('''
                INSERT INTO bullets (experience_id, bullet_text, template_text, tags, category)
                VALUES (?, ?, ?, ?, ?)
            ''', (experience_id, bullet_text, template_text, tags, category))
            return cursor.lastrowid
    
    @staticmethod
    def get_by_id(bullet_id):
        """Get a single bullet by ID"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM bullets WHERE id = ?', (bullet_id,))
        return cursor.fetchone()
    
    @staticmethod
    def get_all():
        """Get all bullets with joined experience info"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            SELECT b.*, e.company_name, e.job_title
            FROM bullets b
            LEFT JOIN experiences e ON b.experience_id = e.id
            ORDER BY b.id DESC
        ''')
        return cursor.fetchall()
    
    @staticmethod
    def get_by_experience(experience_id):
        """Get all bullets for a specific experience"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM bullets WHERE experience_id = ?', (experience_id,))
        return cursor.fetchall()
    
    @staticmethod
    def update(bullet_id, bullet_text, template_text, tags, category):
        """Update a bullet"""
        with get_db_context() as (conn, cursor):
            cursor.execute('''
                UPDATE bullets 
                SET bullet_text = ?, template_text = ?, tags = ?, category = ?
                WHERE id = ?
            ''', (bullet_text, template_text, tags, category, bullet_id))
            return cursor.rowcount > 0
    
    @staticmethod
    def delete(bullet_id):
        """Delete a bullet"""
        with get_db_context() as (conn, cursor):
            cursor.execute('DELETE FROM bullets WHERE id = ?', (bullet_id,))
            return cursor.rowcount > 0
    
    @staticmethod
    def count():
        """Get total number of bullets"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT COUNT(*) FROM bullets')
        return cursor.fetchone()[0]
    
    @staticmethod
    def delete_all():
        """Delete all bullets"""
        with get_db_context() as (conn, cursor):
            cursor.execute('DELETE FROM bullets')
            return cursor.rowcount


class Skill:
    """Skill model"""
    
    @staticmethod
    def create(skill_name, category=''):
        """Create a new skill"""
        with get_db_context() as (conn, cursor):
            cursor.execute('''
                INSERT INTO skills (skill_name, category)
                VALUES (?, ?)
            ''', (skill_name, category))
            return cursor.lastrowid
    
    @staticmethod
    def get_by_id(skill_id):
        """Get a single skill by ID"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM skills WHERE id = ?', (skill_id,))
        return cursor.fetchone()
    
    @staticmethod
    def get_all():
        """Get all skills"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM skills ORDER BY category, skill_name')
        return cursor.fetchall()
    
    @staticmethod
    def update(skill_id, skill_name, category):
        """Update a skill"""
        with get_db_context() as (conn, cursor):
            cursor.execute('''
                UPDATE skills 
                SET skill_name = ?, category = ?
                WHERE id = ?
            ''', (skill_name, category, skill_id))
            return cursor.rowcount > 0
    
    @staticmethod
    def delete(skill_id):
        """Delete a skill"""
        with get_db_context() as (conn, cursor):
            cursor.execute('DELETE FROM skills WHERE id = ?', (skill_id,))
            return cursor.rowcount > 0
    
    @staticmethod
    def count():
        """Get total number of skills"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT COUNT(*) FROM skills')
        return cursor.fetchone()[0]
    
    @staticmethod
    def delete_all():
        """Delete all skills"""
        with get_db_context() as (conn, cursor):
            cursor.execute('DELETE FROM skills')
            return cursor.rowcount


class Education:
    """Education model"""
    
    @staticmethod
    def create(school_name, degree='', field_of_study='', 
               graduation_year='', location=''):
        """Create a new education entry"""
        with get_db_context() as (conn, cursor):
            cursor.execute('''
                INSERT INTO education (school_name, degree, field_of_study, 
                                      graduation_year, location)
                VALUES (?, ?, ?, ?, ?)
            ''', (school_name, degree, field_of_study, graduation_year, location))
            return cursor.lastrowid
    
    @staticmethod
    def get_by_id(edu_id):
        """Get a single education entry by ID"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM education WHERE id = ?', (edu_id,))
        return cursor.fetchone()
    
    @staticmethod
    def get_all():
        """Get all education entries"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM education ORDER BY graduation_year DESC')
        return cursor.fetchall()
    
    @staticmethod
    def update(edu_id, school_name, degree, field_of_study, 
               graduation_year, location):
        """Update an education entry"""
        with get_db_context() as (conn, cursor):
            cursor.execute('''
                UPDATE education 
                SET school_name = ?, degree = ?, field_of_study = ?, 
                    graduation_year = ?, location = ?
                WHERE id = ?
            ''', (school_name, degree, field_of_study, graduation_year, location, edu_id))
            return cursor.rowcount > 0
    
    @staticmethod
    def delete(edu_id):
        """Delete an education entry"""
        with get_db_context() as (conn, cursor):
            cursor.execute('DELETE FROM education WHERE id = ?', (edu_id,))
            return cursor.rowcount > 0
    
    @staticmethod
    def count():
        """Get total number of education entries"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT COUNT(*) FROM education')
        return cursor.fetchone()[0]
    
    @staticmethod
    def delete_all():
        """Delete all education entries"""
        with get_db_context() as (conn, cursor):
            cursor.execute('DELETE FROM education')
            return cursor.rowcount
