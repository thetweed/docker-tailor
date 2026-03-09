"""
Export Transform Service - Applies export profile rules to resume data
"""
import copy


def apply_export_rules(experiences, bullets, skills, education, rules):
    """
    Apply export rules to resume data, returning transformed copies.

    Args:
        experiences: list of dicts (converted from sqlite3.Row)
        bullets: list of dicts
        skills: list of dicts
        education: list of dicts
        rules: list of rule dicts, each with 'rule_type', 'config' (parsed dict), 'enabled'

    Returns:
        dict with keys: 'experiences', 'bullets', 'skills', 'education', 'section_order'
    """
    data = {
        'experiences': copy.deepcopy(experiences),
        'bullets': copy.deepcopy(bullets),
        'skills': copy.deepcopy(skills),
        'education': copy.deepcopy(education),
        'section_order': ['experience', 'skills', 'education'],
    }

    for rule in rules:
        if not rule.get('enabled', True):
            continue

        rule_type = rule['rule_type']
        config = rule['config']

        handler = RULE_HANDLERS.get(rule_type)
        if handler:
            handler(data, config)

    return data


def _get_target_items(data, config):
    """Return the item list for the rule's target section (default: 'skills')."""
    return data.get(config.get('target', 'skills'), [])


def _set_experience_field(data, exp_id, field, value):
    """Find an experience by ID and set a single field on it."""
    for exp in data['experiences']:
        if exp.get('id') == exp_id:
            exp[field] = value
            break


def _apply_rename_category(data, config):
    """Rename a category on skills or bullets."""
    from_name = config.get('from_name', '')
    to_name = config.get('to_name', '')

    if not from_name or not to_name:
        return

    for item in _get_target_items(data, config):
        if item.get('category') == from_name:
            item['category'] = to_name


def _apply_merge_categories(data, config):
    """Merge multiple categories into one."""
    source_categories = config.get('source_categories', [])
    destination = config.get('destination_category', '')

    if not source_categories or not destination:
        return

    source_set = set(source_categories)
    for item in _get_target_items(data, config):
        if item.get('category') in source_set:
            item['category'] = destination


def _apply_split_category(data, config):
    """Split skills into sub-categories based on skill IDs.

    Note: despite the generic 'target' config key, the 'splits' entries use
    'skill_ids' — this rule only applies meaningfully to the skills section.
    """
    splits = config.get('splits', [])

    if not splits:
        return

    # Build a mapping: item_id -> new_category
    id_to_category = {}
    for split in splits:
        new_cat = split.get('new_category', '')
        for item_id in split.get('skill_ids', []):
            id_to_category[item_id] = new_cat

    for item in _get_target_items(data, config):
        item_id = item.get('id')
        if item_id in id_to_category:
            item['category'] = id_to_category[item_id]


def _apply_section_order(data, config):
    """Set the section rendering order."""
    order = config.get('order', [])
    if order:
        data['section_order'] = order


def _apply_use_alternate_title(data, config):
    """Replace an experience's job_title with an alternate title."""
    exp_id = config.get('experience_id')
    title = config.get('title', '')

    if exp_id is None or not title:
        return

    _set_experience_field(data, exp_id, 'job_title', title)


def _apply_rename_company(data, config):
    """Replace an experience's company_name with a display name."""
    exp_id = config.get('experience_id')
    display_name = config.get('display_name', '')

    if exp_id is None or not display_name:
        return

    _set_experience_field(data, exp_id, 'company_name', display_name)


RULE_HANDLERS = {
    'rename_category': _apply_rename_category,
    'merge_categories': _apply_merge_categories,
    'split_category': _apply_split_category,
    'section_order': _apply_section_order,
    'use_alternate_title': _apply_use_alternate_title,
    'rename_company': _apply_rename_company,
}
