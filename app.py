#!/usr/bin/env python3
"""
Flask Job Application Tracker
An AI-powered job application tracking system
"""
import os
from flask import Flask
from flask_session import Session
from flask_wtf.csrf import CSRFProtect
from config import config
import models.database as database

csrf = CSRFProtect()

def create_app(config_name='default'):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
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
    
    return app


def check_environment():
    """Check that environment is properly configured"""
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("\n⚠️  WARNING: ANTHROPIC_API_KEY not found in environment variables!")
        print("Please create a .env file with your API key.")
        print("See .env.example for template.\n")
        return False
    else:
        print("✓ API key found")
        return True


if __name__ == '__main__':
    # Check environment
    env_ok = check_environment()
    
    # Create app
    app = create_app('development')
    
    print("\n🚀 Starting Job Tracker...")
    print("📍 Open your browser to: http://127.0.0.1:5000\n")
    
    if not env_ok:
        print("⚠️  Warning: Application may not work correctly without API key\n")
    
    # Run the app
    app.run(host='0.0.0.0', debug=True, port=5000)