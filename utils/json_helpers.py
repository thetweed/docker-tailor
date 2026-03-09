"""JSON utility helpers shared across models."""
import json
import logging

logger = logging.getLogger(__name__)


def ensure_json_string(value):
    """Convert a dict to a JSON string; pass strings through unchanged."""
    return json.dumps(value) if isinstance(value, dict) else value


def safe_json_loads(s, context='', default=None):
    """Parse JSON safely, logging errors and returning default on failure.

    Args:
        s: JSON string to parse (or None/non-string — handled gracefully)
        context: Short description for the error log (e.g. 'rule id=5')
        default: Value to return on failure (defaults to {})
    """
    if default is None:
        default = {}
    try:
        return json.loads(s)
    except (json.JSONDecodeError, TypeError):
        ctx = f' ({context})' if context else ''
        logger.error("Corrupted JSON%s: %.100r", ctx, s)
        return default
