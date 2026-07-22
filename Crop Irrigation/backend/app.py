import os
from flask import Flask, send_from_directory
from backend.config import Config
from backend.database import init_db
from backend.routes import api

# Find absolute path of the frontend directory
backend_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(backend_dir)
frontend_dir = os.path.join(root_dir, 'frontend')

# Initialize Flask app
# Map the static folder to frontend so that css/js files are auto-served
app = Flask(__name__, static_folder=frontend_dir, static_url_path='')
app.config.from_object(Config)

# Initialize database schema and seeds
init_db()

# Register APIs
app.register_blueprint(api, url_prefix='/api')

# Frontend page endpoints
@app.route('/')
def index():
    return send_from_directory(frontend_dir, 'index.html')

@app.route('/login.html')
@app.route('/login')
def login_page():
    return send_from_directory(frontend_dir, 'login.html')

@app.route('/register.html')
@app.route('/register')
def register_page():
    return send_from_directory(frontend_dir, 'register.html')

@app.route('/dashboard.html')
@app.route('/dashboard')
def dashboard_page():
    return send_from_directory(frontend_dir, 'dashboard.html')

@app.route('/upload.html')
@app.route('/upload')
def upload_page():
    return send_from_directory(frontend_dir, 'upload.html')

@app.route('/result.html')
@app.route('/result')
def result_page():
    return send_from_directory(frontend_dir, 'result.html')

# Start server
if __name__ == '__main__':
    # Ensure application upload folders are created
    os.makedirs(os.path.join(Config.UPLOAD_FOLDER, 'original_images'), exist_ok=True)
    os.makedirs(os.path.join(Config.UPLOAD_FOLDER, 'processed_images'), exist_ok=True)
    os.makedirs(os.path.join(Config.UPLOAD_FOLDER, 'prediction_results'), exist_ok=True)
    
    print(f"Starting Crop Irrigation System on http://localhost:5000")
    app.run(host='127.0.0.1', port=5000, debug=True)
