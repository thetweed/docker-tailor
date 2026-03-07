"""
Application Configuration
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration"""
    
    # Flask
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY')

    # Optional password gate — set LOGIN_PASSWORD to require a password to access the app.
    # Leave unset to disable auth (useful for local dev).
    LOGIN_PASSWORD = os.getenv('LOGIN_PASSWORD')
    
    # Session
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = 'flask_session'
    SESSION_PERMANENT = False
    
    # File Upload
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # Database
    DATABASE_DIR = os.getenv('DATABASE_DIR', 'data')
    DATABASE_NAME = os.path.join(DATABASE_DIR, 'jobs.db')
    
    # API
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    
    # AI Models
    HAIKU_MODEL = "claude-haiku-4-5-20251001"
    SONNET_MODEL = "claude-sonnet-4-5-20250929"
    
    # Scraping
    SCRAPE_TIMEOUT = 60000  # milliseconds
    SCRAPE_WAIT_TIME = 3000  # milliseconds
    
    @staticmethod
    def init_app(app):
        """Initialize application with this config"""
        if not app.config.get('SECRET_KEY'):
            raise ValueError(
                "FLASK_SECRET_KEY is not set. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        # Create necessary directories
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.SESSION_FILE_DIR, exist_ok=True)
        os.makedirs(Config.DATABASE_DIR, exist_ok=True)


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Production-specific initialization
        if not cls.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY must be set in production")


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': ProductionConfig
}