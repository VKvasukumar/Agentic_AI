import os

class Config:
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-crop-irrigation-secret-key-987654321')
    DEBUG = True
    
    # Paths configuration
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    DATABASE_PATH = os.path.join(BASE_DIR, 'database', 'crop_irrigation.db')
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    
    # Upload limits and types
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB limit
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
