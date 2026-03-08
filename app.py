#!/usr/bin/env python3
"""
Flask Job Application Tracker
An AI-powered job application tracking system
"""
import logging
import os
from flask import Flask, session, redirect, url_for, request
from flask_session import Session
from flask_wtf.csrf import CSRFProtect
from config import config
import models.database as database

logger = logging.getLogger(__name__)

csrf = CSRFProtect()

# Endpoints that don't require authentication
_AUTH_EXEMPT = {'main.login', 'main.logout', 'static'}


def create_app(config_name=None):
    """Application factory pattern"""
    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'default')
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s: %(message)s'
    )

    # Initialize Flask-Session
    Session(app)

    # Initialize CSRF protection
    csrf.init_app(app)

    # Initialize database
    database.init_app(app)

    # Register blueprints
    from routes import main, jobs, resume, export, suggestions, tailoring

    app.register_blueprint(main.bp)
    app.register_blueprint(jobs.bp)
    app.register_blueprint(resume.bp)
    app.register_blueprint(export.bp)
    app.register_blueprint(suggestions.bp)
    app.register_blueprint(tailoring.bp)

    # Security headers on every response
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "frame-ancestors 'none'"
        )
        return response

    # Password gate — only active when LOGIN_PASSWORD is configured
    @app.before_request
    def check_auth():
        if request.endpoint in _AUTH_EXEMPT:
            return
        login_password = app.config.get('LOGIN_PASSWORD')
        if not login_password:
            return  # Auth disabled
        if not session.get('authenticated'):
            return redirect(url_for('main.login', next=request.path))

    return app


def check_environment():
    """Check that environment is properly configured"""
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not found in environment variables — please set it in .env")
        return False
    return True


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(levelname)s %(name)s: %(message)s'
    )

    # Check environment
    env_ok = check_environment()

    # Create app (local dev only — Docker uses gunicorn)
    app = create_app('development')

    logger.info("Starting Job Tracker — open http://127.0.0.1:5000")

    if not env_ok:
        logger.warning("Application may not work correctly without API key")

    # Run the app — development only, never use this in production
    app.run(host='127.0.0.1', debug=True, port=5000)
