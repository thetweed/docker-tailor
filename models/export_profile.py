"""
Export Profile Model - Database operations for export profiles and rules
"""
import json
import logging
from models.database import get_db_context, get_db

logger = logging.getLogger(__name__)


class ExportProfile:
    """Export profile and rules model"""

    # Rule type constants
    RULE_RENAME_CATEGORY = 'rename_category'
    RULE_MERGE_CATEGORIES = 'merge_categories'
    RULE_SPLIT_CATEGORY = 'split_category'
    RULE_SECTION_ORDER = 'section_order'
    RULE_USE_ALTERNATE_TITLE = 'use_alternate_title'

    RULE_TYPES = [
        RULE_RENAME_CATEGORY,
        RULE_MERGE_CATEGORIES,
        RULE_SPLIT_CATEGORY,
        RULE_SECTION_ORDER,
        RULE_USE_ALTERNATE_TITLE,
    ]

    # Human-readable rule type labels
    RULE_TYPE_LABELS = {
        RULE_RENAME_CATEGORY: 'Rename Category',
        RULE_MERGE_CATEGORIES: 'Merge Categories',
        RULE_SPLIT_CATEGORY: 'Split Category',
        RULE_SECTION_ORDER: 'Section Order',
        RULE_USE_ALTERNATE_TITLE: 'Use Alternate Title',
    }

    # --- Profile CRUD ---

    @staticmethod
    def create(name, description=''):
        """Create a new export profile"""
        with get_db_context() as (conn, cursor):
            cursor.execute('''
                INSERT INTO export_profiles (name, description)
                VALUES (?, ?)
            ''', (name, description))
            return cursor.lastrowid

    @staticmethod
    def get_by_id(profile_id):
        """Get a single profile by ID"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM export_profiles WHERE id = ?', (profile_id,))
        return cursor.fetchone()

    @staticmethod
    def get_all():
        """Get all profiles ordered by name"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM export_profiles ORDER BY name')
        return cursor.fetchall()

    @staticmethod
    def update(profile_id, name, description='', header_info=None):
        """Update profile name, description, and optionally header_info"""
        with get_db_context() as (conn, cursor):
            if header_info is not None:
                header_json = json.dumps(header_info) if isinstance(header_info, dict) else header_info
                cursor.execute('''
                    UPDATE export_profiles
                    SET name = ?, description = ?, header_info = ?, date_modified = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (name, description, header_json, profile_id))
            else:
                cursor.execute('''
                    UPDATE export_profiles
                    SET name = ?, description = ?, date_modified = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (name, description, profile_id))
            return cursor.rowcount > 0

    @staticmethod
    def update_header_info(profile_id, header_info):
        """Update only the header_info for a profile"""
        header_json = json.dumps(header_info) if isinstance(header_info, dict) else header_info
        with get_db_context() as (conn, cursor):
            cursor.execute('''
                UPDATE export_profiles
                SET header_info = ?, date_modified = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (header_json, profile_id))
            return cursor.rowcount > 0

    @staticmethod
    def get_header_info(profile_id):
        """Get parsed header_info dict for a profile"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT header_info FROM export_profiles WHERE id = ?', (profile_id,))
        row = cursor.fetchone()
        if row and row['header_info']:
            return json.loads(row['header_info'])
        return {}

    @staticmethod
    def delete(profile_id):
        """Delete a profile and all its rules"""
        with get_db_context() as (conn, cursor):
            cursor.execute('DELETE FROM export_rules WHERE profile_id = ?', (profile_id,))
            cursor.execute('DELETE FROM export_profiles WHERE id = ?', (profile_id,))
            return cursor.rowcount

    @staticmethod
    def set_default(profile_id):
        """Set a profile as the default, clearing any existing default"""
        with get_db_context() as (conn, cursor):
            cursor.execute('UPDATE export_profiles SET is_default = 0')
            cursor.execute('UPDATE export_profiles SET is_default = 1 WHERE id = ?', (profile_id,))
            return cursor.rowcount > 0

    @staticmethod
    def clear_default():
        """Clear the default profile"""
        with get_db_context() as (conn, cursor):
            cursor.execute('UPDATE export_profiles SET is_default = 0')

    @staticmethod
    def get_default():
        """Get the default profile, or None"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM export_profiles WHERE is_default = 1')
        return cursor.fetchone()

    @staticmethod
    def duplicate(profile_id, new_name):
        """Duplicate a profile with all its rules under a new name"""
        with get_db_context() as (conn, cursor):
            # Get original profile
            cursor.execute('SELECT * FROM export_profiles WHERE id = ?', (profile_id,))
            original = cursor.fetchone()
            if not original:
                return None

            # Create new profile
            cursor.execute('''
                INSERT INTO export_profiles (name, description, header_info)
                VALUES (?, ?, ?)
            ''', (new_name, original['description'], original['header_info']))
            new_id = cursor.lastrowid

            # Copy rules
            cursor.execute('''
                SELECT rule_type, rule_order, config, enabled
                FROM export_rules WHERE profile_id = ?
                ORDER BY rule_order
            ''', (profile_id,))
            rules = cursor.fetchall()

            for rule in rules:
                cursor.execute('''
                    INSERT INTO export_rules (profile_id, rule_type, rule_order, config, enabled)
                    VALUES (?, ?, ?, ?, ?)
                ''', (new_id, rule['rule_type'], rule['rule_order'],
                      rule['config'], rule['enabled']))

            return new_id

    # --- Rule CRUD ---

    @staticmethod
    def add_rule(profile_id, rule_type, config, enabled=True):
        """Add a rule to a profile. Config should be a dict (will be JSON-serialized)."""
        with get_db_context() as (conn, cursor):
            # Auto-assign rule_order as max+1
            cursor.execute(
                'SELECT COALESCE(MAX(rule_order), -1) + 1 FROM export_rules WHERE profile_id = ?',
                (profile_id,))
            next_order = cursor.fetchone()[0]

            config_json = json.dumps(config) if isinstance(config, dict) else config
            cursor.execute('''
                INSERT INTO export_rules (profile_id, rule_type, rule_order, config, enabled)
                VALUES (?, ?, ?, ?, ?)
            ''', (profile_id, rule_type, next_order, config_json, 1 if enabled else 0))

            # Update profile modified timestamp
            cursor.execute(
                'UPDATE export_profiles SET date_modified = CURRENT_TIMESTAMP WHERE id = ?',
                (profile_id,))

            return cursor.lastrowid

    @staticmethod
    def get_rules(profile_id):
        """Get all rules for a profile, ordered by rule_order"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            SELECT * FROM export_rules
            WHERE profile_id = ?
            ORDER BY rule_order
        ''', (profile_id,))
        return cursor.fetchall()

    @staticmethod
    def get_rule_by_id(rule_id):
        """Get a single rule by ID"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM export_rules WHERE id = ?', (rule_id,))
        return cursor.fetchone()

    @staticmethod
    def update_rule(rule_id, config=None, enabled=None):
        """Update a rule's config and/or enabled state"""
        with get_db_context() as (conn, cursor):
            if config is not None and enabled is not None:
                config_json = json.dumps(config) if isinstance(config, dict) else config
                cursor.execute('''
                    UPDATE export_rules SET config = ?, enabled = ? WHERE id = ?
                ''', (config_json, 1 if enabled else 0, rule_id))
            elif config is not None:
                config_json = json.dumps(config) if isinstance(config, dict) else config
                cursor.execute(
                    'UPDATE export_rules SET config = ? WHERE id = ?',
                    (config_json, rule_id))
            elif enabled is not None:
                cursor.execute(
                    'UPDATE export_rules SET enabled = ? WHERE id = ?',
                    (1 if enabled else 0, rule_id))

            # Update parent profile's modified timestamp
            cursor.execute('''
                UPDATE export_profiles SET date_modified = CURRENT_TIMESTAMP
                WHERE id = (SELECT profile_id FROM export_rules WHERE id = ?)
            ''', (rule_id,))

            return cursor.rowcount > 0

    @staticmethod
    def delete_rule(rule_id):
        """Delete a rule"""
        with get_db_context() as (conn, cursor):
            # Get profile_id before deleting
            cursor.execute('SELECT profile_id FROM export_rules WHERE id = ?', (rule_id,))
            row = cursor.fetchone()
            profile_id = row['profile_id'] if row else None

            cursor.execute('DELETE FROM export_rules WHERE id = ?', (rule_id,))

            if profile_id:
                cursor.execute(
                    'UPDATE export_profiles SET date_modified = CURRENT_TIMESTAMP WHERE id = ?',
                    (profile_id,))

            return cursor.rowcount

    @staticmethod
    def toggle_rule(rule_id):
        """Toggle a rule's enabled state"""
        with get_db_context() as (conn, cursor):
            cursor.execute('''
                UPDATE export_rules SET enabled = CASE WHEN enabled = 1 THEN 0 ELSE 1 END
                WHERE id = ?
            ''', (rule_id,))
            return cursor.rowcount > 0

    @staticmethod
    def reorder_rules(profile_id, rule_id_order):
        """Reorder rules by a list of rule IDs in desired order"""
        with get_db_context() as (conn, cursor):
            for idx, rule_id in enumerate(rule_id_order):
                cursor.execute('''
                    UPDATE export_rules SET rule_order = ?
                    WHERE id = ? AND profile_id = ?
                ''', (idx, rule_id, profile_id))

            cursor.execute(
                'UPDATE export_profiles SET date_modified = CURRENT_TIMESTAMP WHERE id = ?',
                (profile_id,))

    @staticmethod
    def get_rule_count(profile_id):
        """Get the number of rules in a profile"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT COUNT(*) FROM export_rules WHERE profile_id = ?', (profile_id,))
        return cursor.fetchone()[0]

    # --- Composite helpers ---

    @staticmethod
    def get_profile_with_rules(profile_id):
        """Get a profile with its rules (configs parsed from JSON)"""
        db = get_db()
        cursor = db.cursor()

        cursor.execute('SELECT * FROM export_profiles WHERE id = ?', (profile_id,))
        profile = cursor.fetchone()
        if not profile:
            return None

        cursor.execute('''
            SELECT * FROM export_rules
            WHERE profile_id = ?
            ORDER BY rule_order
        ''', (profile_id,))
        raw_rules = cursor.fetchall()

        rules = []
        for rule in raw_rules:
            try:
                config = json.loads(rule['config'])
            except (json.JSONDecodeError, TypeError):
                logger.error("Corrupted config for export rule id=%s", rule['id'])
                config = {}
            rules.append({
                'id': rule['id'],
                'profile_id': rule['profile_id'],
                'rule_type': rule['rule_type'],
                'rule_order': rule['rule_order'],
                'config': config,
                'enabled': bool(rule['enabled']),
            })

        header_info = {}
        if profile['header_info']:
            try:
                header_info = json.loads(profile['header_info'])
            except (json.JSONDecodeError, TypeError):
                pass

        return {
            'profile': profile,
            'rules': rules,
            'header_info': header_info,
        }

    @staticmethod
    def get_all_with_rule_counts():
        """Get all profiles with their rule counts"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            SELECT p.*, COUNT(r.id) as rule_count
            FROM export_profiles p
            LEFT JOIN export_rules r ON p.id = r.profile_id
            GROUP BY p.id
            ORDER BY p.name
        ''')
        return cursor.fetchall()

    @staticmethod
    def describe_rule(rule_type, config):
        """Return a human-readable description of a rule"""
        if isinstance(config, str):
            config = json.loads(config)

        if rule_type == ExportProfile.RULE_RENAME_CATEGORY:
            target = config.get('target', 'skills')
            return f"Rename {target} category \"{config.get('from_name', '')}\" to \"{config.get('to_name', '')}\""

        elif rule_type == ExportProfile.RULE_MERGE_CATEGORIES:
            target = config.get('target', 'skills')
            sources = ', '.join(f'"{s}"' for s in config.get('source_categories', []))
            dest = config.get('destination_category', '')
            return f"Merge {target} categories {sources} into \"{dest}\""

        elif rule_type == ExportProfile.RULE_SPLIT_CATEGORY:
            source = config.get('source_category', '')
            splits = config.get('splits', [])
            new_cats = ', '.join(f'"{s["new_category"]}"' for s in splits)
            return f"Split \"{source}\" into {new_cats}"

        elif rule_type == ExportProfile.RULE_SECTION_ORDER:
            order = config.get('order', [])
            return f"Section order: {' > '.join(o.title() for o in order)}"

        elif rule_type == ExportProfile.RULE_USE_ALTERNATE_TITLE:
            title = config.get('title', '')
            exp_id = config.get('experience_id', '?')
            return f"Use title \"{title}\" for experience #{exp_id}"

        return f"Unknown rule: {rule_type}"
