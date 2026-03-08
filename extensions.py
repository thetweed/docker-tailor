"""
Flask extension instances — imported by both app.py and blueprints to avoid circular imports.
"""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Key on remote IP. For a single-user personal tool this is the simplest approach;
# all limits below are generous enough that normal use never approaches them.
limiter = Limiter(key_func=get_remote_address, default_limits=[])
