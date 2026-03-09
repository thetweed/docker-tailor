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
        """Delete an experience and its associated bullets"""
        with get_db_context() as (conn, cursor):
            cursor.execute('DELETE FROM bullets WHERE experience_id = ?', (exp_id,))
            cursor.execute('DELETE FROM experiences WHERE id = ?', (exp_id,))
            return cursor.rowcount
    
    @staticmethod
    def count():
        """Get total number of experiences"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT COUNT(*) FROM experiences')
        return cursor.fetchone()[0]
    
    @staticmethod
    def exists(company_name, job_title):
        """Return True if an experience with matching company and title already exists (case-insensitive)"""
        return Experience.get_existing_id(company_name, job_title) is not None

    @staticmethod
    def get_existing_id(company_name, job_title):
        """Return the id of a matching experience, or None (case-insensitive)"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "SELECT id FROM experiences WHERE LOWER(company_name) = LOWER(?) AND LOWER(job_title) = LOWER(?)",
            (company_name, job_title)
        )
        row = cursor.fetchone()
        return row['id'] if row else None

    @staticmethod
    def delete_all():
        """Delete all experiences and their associated bullets"""
        with get_db_context() as (conn, cursor):
            cursor.execute('DELETE FROM bullets WHERE experience_id IS NOT NULL')
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
        """Get all bullets with joined experience and group info"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            SELECT b.*, e.company_name, e.job_title, bg.label as group_label
            FROM bullets b
            LEFT JOIN experiences e ON b.experience_id = e.id
            LEFT JOIN bullet_groups bg ON b.group_id = bg.id
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
    def update(bullet_id, bullet_text, template_text, tags, category, experience_id=None):
        """Update a bullet"""
        with get_db_context() as (conn, cursor):
            cursor.execute('''
                UPDATE bullets
                SET bullet_text = ?, template_text = ?, tags = ?, category = ?, experience_id = ?
                WHERE id = ?
            ''', (bullet_text, template_text, tags, category, experience_id, bullet_id))
            return cursor.rowcount > 0
    
    @staticmethod
    def delete(bullet_id):
        """Delete a bullet, auto-promoting another group member if it was the default"""
        with get_db_context() as (conn, cursor):
            cursor.execute('SELECT group_id, is_group_default FROM bullets WHERE id = ?', (bullet_id,))
            row = cursor.fetchone()
            if row and row['group_id'] and row['is_group_default']:
                # Promote another bullet in the same group to default
                cursor.execute(
                    'UPDATE bullets SET is_group_default = 1 WHERE id = '
                    '(SELECT id FROM bullets WHERE group_id = ? AND id != ? LIMIT 1)',
                    (row['group_id'], bullet_id)
                )
            cursor.execute('DELETE FROM bullets WHERE id = ?', (bullet_id,))
            return cursor.rowcount

    @staticmethod
    def set_group(bullet_id, group_id, is_default):
        """Assign a bullet to a group (or remove it from a group if group_id is None)"""
        with get_db_context() as (conn, cursor):
            if group_id is not None and is_default:
                cursor.execute('UPDATE bullets SET is_group_default = 0 WHERE group_id = ?', (group_id,))
            cursor.execute(
                'UPDATE bullets SET group_id = ?, is_group_default = ? WHERE id = ?',
                (group_id, 1 if is_default else 0, bullet_id)
            )

    @staticmethod
    def set_group_default(bullet_id):
        """Make this bullet the default for its group"""
        with get_db_context() as (conn, cursor):
            cursor.execute('SELECT group_id FROM bullets WHERE id = ?', (bullet_id,))
            row = cursor.fetchone()
            if not row or not row['group_id']:
                return False
            group_id = row['group_id']
            cursor.execute('UPDATE bullets SET is_group_default = 0 WHERE group_id = ?', (group_id,))
            cursor.execute('UPDATE bullets SET is_group_default = 1 WHERE id = ?', (bullet_id,))
            return True
    
    @staticmethod
    def count():
        """Get total number of bullets"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT COUNT(*) FROM bullets')
        return cursor.fetchone()[0]
    
    @staticmethod
    def exists(bullet_text):
        """Return True if a bullet with matching text already exists (case-insensitive)"""
        return Bullet.get_existing_id(bullet_text) is not None

    @staticmethod
    def get_existing_id(bullet_text):
        """Return the id of a matching bullet, or None (case-insensitive)"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "SELECT id FROM bullets WHERE LOWER(bullet_text) = LOWER(?)",
            (bullet_text,)
        )
        row = cursor.fetchone()
        return row['id'] if row else None

    @staticmethod
    def delete_all():
        """Delete all bullets and their groups"""
        with get_db_context() as (conn, cursor):
            cursor.execute('DELETE FROM bullets')
            cursor.execute('DELETE FROM bullet_groups')
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
    def get_categories():
        """Get sorted list of distinct non-empty category names"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "SELECT DISTINCT category FROM skills "
            "WHERE category IS NOT NULL AND category != '' "
            "ORDER BY category"
        )
        return [row['category'] for row in cursor.fetchall()]

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
            return cursor.rowcount
    
    @staticmethod
    def count():
        """Get total number of skills"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT COUNT(*) FROM skills')
        return cursor.fetchone()[0]
    
    @staticmethod
    def exists(skill_name):
        """Return True if a skill with matching name already exists (case-insensitive)"""
        return Skill.get_existing_id(skill_name) is not None

    @staticmethod
    def get_existing_id(skill_name):
        """Return the id of a matching skill, or None (case-insensitive)"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "SELECT id FROM skills WHERE LOWER(skill_name) = LOWER(?)",
            (skill_name,)
        )
        row = cursor.fetchone()
        return row['id'] if row else None

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
            return cursor.rowcount
    
    @staticmethod
    def count():
        """Get total number of education entries"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT COUNT(*) FROM education')
        return cursor.fetchone()[0]
    
    @staticmethod
    def exists(school_name, degree, field_of_study):
        """Return True if a matching education entry already exists (case-insensitive)"""
        return Education.get_existing_id(school_name, degree, field_of_study) is not None

    @staticmethod
    def get_existing_id(school_name, degree, field_of_study):
        """Return the id of a matching education entry, or None (case-insensitive)"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "SELECT id FROM education WHERE LOWER(school_name) = LOWER(?) "
            "AND LOWER(degree) = LOWER(?) AND LOWER(field_of_study) = LOWER(?)",
            (school_name, degree, field_of_study)
        )
        row = cursor.fetchone()
        return row['id'] if row else None

    @staticmethod
    def delete_all():
        """Delete all education entries"""
        with get_db_context() as (conn, cursor):
            cursor.execute('DELETE FROM education')
            return cursor.rowcount


def get_all_components():
    """Fetch all four resume component tables in one context and return them as a tuple.

    Returns:
        (experiences, bullets, skills, education) — all as sqlite3.Row lists.
        Bullets are ordered by experience_id then id for grouping convenience.
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM experiences ORDER BY id")
    experiences = cursor.fetchall()
    cursor.execute("SELECT * FROM bullets ORDER BY experience_id, id")
    bullets = cursor.fetchall()
    cursor.execute("SELECT * FROM skills ORDER BY category, skill_name")
    skills = cursor.fetchall()
    cursor.execute("SELECT * FROM education ORDER BY id")
    education = cursor.fetchall()
    return experiences, bullets, skills, education


class BulletGroup:
    """Group of alternate-wording bullet points"""

    @staticmethod
    def create(label=None):
        """Create a new bullet group"""
        with get_db_context() as (conn, cursor):
            cursor.execute('INSERT INTO bullet_groups (label) VALUES (?)', (label,))
            return cursor.lastrowid

    @staticmethod
    def get_all():
        """Get all bullet groups with member count"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            SELECT bg.*, COUNT(b.id) as bullet_count
            FROM bullet_groups bg
            LEFT JOIN bullets b ON b.group_id = bg.id
            GROUP BY bg.id
            ORDER BY bg.id
        ''')
        return cursor.fetchall()

    @staticmethod
    def delete(group_id):
        """Ungroup all member bullets then delete the group"""
        with get_db_context() as (conn, cursor):
            cursor.execute(
                'UPDATE bullets SET group_id = NULL, is_group_default = 1 WHERE group_id = ?',
                (group_id,)
            )
            cursor.execute('DELETE FROM bullet_groups WHERE id = ?', (group_id,))
            return cursor.rowcount
