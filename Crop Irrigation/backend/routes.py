import os
import json
import sqlite3
from flask import Blueprint, request, jsonify, session, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from backend.config import Config
from backend.database import get_db
from ai_model.predict import predict_irrigation_recommendation, predict_crop_disease

api = Blueprint('api', __name__)

def get_current_user():
    """Helper to get logged-in user or auto-login seed user if in development."""
    user_id = session.get('user_id')
    if not user_id:
        # Auto-login fallback for developer convenience (seeded user ID is 1)
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE id = 1").fetchone()
        db.close()
        if user:
            session['user_id'] = user['id']
            return user['id']
        return None
    return user_id

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@api.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    farm_name = data.get('farm_name', 'My Farm')
    location = data.get('location', 'Unknown')
    crop_type = data.get('crop_type', 'Tomato')
    farm_size = data.get('farm_size', 1.0)
    
    if not username or not email or not password:
        return jsonify({"error": "Missing username, email, or password"}), 400
        
    password_hash = generate_password_hash(password)
    
    db = get_db()
    try:
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, password_hash)
        )
        user_id = cursor.lastrowid
        
        cursor.execute(
            "INSERT INTO farms (user_id, farm_name, location, crop_type, farm_size) VALUES (?, ?, ?, ?, ?)",
            (user_id, farm_name, location, crop_type, float(farm_size))
        )
        db.commit()
        session['user_id'] = user_id
        return jsonify({"message": "Registration successful", "user_id": user_id}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username or Email already exists"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@api.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400
        
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    db.close()
    
    if user and check_password_hash(user['password_hash'], password):
        session['user_id'] = user['id']
        return jsonify({"message": "Login successful", "user_id": user['id']})
    
    return jsonify({"error": "Invalid username or password"}), 401

@api.route('/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"message": "Logout successful"})

@api.route('/auth/me', methods=['GET'])
def me():
    user_id = get_current_user()
    if not user_id:
        return jsonify({"logged_in": False}), 401
        
    db = get_db()
    user = db.execute("SELECT id, username, email FROM users WHERE id = ?", (user_id,)).fetchone()
    farm = db.execute("SELECT * FROM farms WHERE user_id = ?", (user_id,)).fetchone()
    db.close()
    
    if not user:
        session.clear()
        return jsonify({"logged_in": False}), 401
        
    return jsonify({
        "logged_in": True,
        "user": {
            "id": user['id'],
            "username": user['username'],
            "email": user['email']
        },
        "farm": {
            "id": farm['id'] if farm else None,
            "farm_name": farm['farm_name'] if farm else "N/A",
            "location": farm['location'] if farm else "N/A",
            "crop_type": farm['crop_type'] if farm else "N/A",
            "farm_size": farm['farm_size'] if farm else 0.0
        }
    })

@api.route('/dashboard/stats', methods=['GET'])
def dashboard_stats():
    user_id = get_current_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
        
    db = get_db()
    farm = db.execute("SELECT * FROM farms WHERE user_id = ?", (user_id,)).fetchone()
    if not farm:
        db.close()
        return jsonify({"error": "No farm associated with user"}), 404
        
    # Get latest soil reading
    soil = db.execute(
        "SELECT * FROM soil_readings WHERE farm_id = ? ORDER BY recorded_at DESC LIMIT 1",
        (farm['id'],)
    ).fetchone()
    
    # Get latest weather reading
    weather = db.execute(
        "SELECT * FROM weather_readings WHERE farm_id = ? ORDER BY recorded_at DESC LIMIT 1",
        (farm['id'],)
    ).fetchone()
    
    # Get pump status (last event in history)
    last_irrigation = db.execute(
        "SELECT * FROM irrigation_history WHERE farm_id = ? ORDER BY timestamp DESC LIMIT 1",
        (farm['id'],)
    ).fetchone()
    
    pump_status = "OFF"
    if last_irrigation and last_irrigation['action'] == 'pump_on':
        pump_status = "ON"
        
    # Calculate recommendations if we have readings
    recommendation = None
    if soil and weather:
        recommendation = predict_irrigation_recommendation(
            moisture=soil['moisture'],
            temperature=soil['temperature'],
            rainfall=weather['rainfall'],
            forecast=weather['forecast'],
            crop_type=farm['crop_type'],
            farm_size_acres=farm['farm_size']
        )
    else:
        # Fallback values if DB was somehow unseeded
        recommendation = {
            "status": "No Data",
            "water_volume_liters": 0,
            "duration_minutes": 0,
            "reason": "Please register soil and weather readings to receive recommendations.",
            "confidence": 0.0
        }
        
    # Get 3 recent predictions
    recent_preds = db.execute(
        "SELECT * FROM predictions WHERE farm_id = ? ORDER BY created_at DESC LIMIT 3",
        (farm['id'],)
    ).fetchall()
    
    predictions_list = []
    for pred in recent_preds:
        predictions_list.append({
            "id": pred['id'],
            "prediction_type": pred['prediction_type'],
            "inputs": json.loads(pred['inputs']),
            "results": json.loads(pred['results']),
            "confidence": pred['confidence'],
            "created_at": pred['created_at']
        })
        
    # Build dashboard payload
    payload = {
        "crop_type": farm['crop_type'],
        "farm_name": farm['farm_name'],
        "pump_status": pump_status,
        "soil": {
            "moisture": soil['moisture'] if soil else 45.0,
            "temperature": soil['temperature'] if soil else 24.0,
            "ph": soil['ph'] if soil else 6.5,
            "nitrogen": soil['nitrogen'] if soil else 80,
            "phosphorus": soil['phosphorus'] if soil else 40,
            "potassium": soil['potassium'] if soil else 140,
            "recorded_at": soil['recorded_at'] if soil else "N/A"
        },
        "weather": {
            "temperature": weather['temperature'] if weather else 25.0,
            "humidity": weather['humidity'] if weather else 60.0,
            "rainfall": weather['rainfall'] if weather else 0.0,
            "forecast": weather['forecast'] if weather else "sunny",
            "recorded_at": weather['recorded_at'] if weather else "N/A"
        },
        "recommendation": recommendation,
        "recent_predictions": predictions_list
    }
    
    db.close()
    return jsonify(payload)

@api.route('/dashboard/history', methods=['GET'])
def dashboard_history():
    user_id = get_current_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
        
    db = get_db()
    farm = db.execute("SELECT id FROM farms WHERE user_id = ?", (user_id,)).fetchone()
    if not farm:
        db.close()
        return jsonify({"error": "No farm found"}), 404
        
    # Get last 12 readings for graphs
    readings = db.execute(
        "SELECT moisture, temperature, recorded_at FROM soil_readings WHERE farm_id = ? ORDER BY recorded_at DESC LIMIT 12",
        (farm['id'],)
    ).fetchall()
    db.close()
    
    history = []
    # Reverse so they appear chronologically in graphs
    for r in reversed(readings):
        history.append({
            "moisture": r['moisture'],
            "temperature": r['temperature'],
            "time": r['recorded_at'].split(' ')[1][:5] if ' ' in r['recorded_at'] else r['recorded_at']
        })
        
    return jsonify(history)

@api.route('/predict/irrigation', methods=['POST'])
def predict_irrigation():
    user_id = get_current_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
        
    data = request.get_json() or {}
    moisture = data.get('moisture')
    temperature = data.get('temperature')
    ph = data.get('ph', 6.5)
    nitrogen = data.get('nitrogen', 80.0)
    phosphorus = data.get('phosphorus', 40.0)
    potassium = data.get('potassium', 140.0)
    forecast = data.get('forecast', 'sunny')
    rainfall = data.get('rainfall', 0.0)
    
    if moisture is None or temperature is None:
        return jsonify({"error": "Missing moisture or temperature values"}), 400
        
    db = get_db()
    farm = db.execute("SELECT * FROM farms WHERE user_id = ?", (user_id,)).fetchone()
    if not farm:
        db.close()
        return jsonify({"error": "No farm found"}), 404
        
    # Run prediction logic
    rec = predict_irrigation_recommendation(
        moisture=float(moisture),
        temperature=float(temperature),
        rainfall=float(rainfall),
        forecast=forecast,
        crop_type=farm['crop_type'],
        farm_size_acres=farm['farm_size']
    )
    
    # Save reading to soil_readings
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO soil_readings (farm_id, moisture, temperature, ph, nitrogen, phosphorus, potassium) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (farm['id'], float(moisture), float(temperature), float(ph), float(nitrogen), float(phosphorus), float(potassium))
    )
    
    # Save weather reading
    cursor.execute(
        "INSERT INTO weather_readings (farm_id, temperature, humidity, rainfall, forecast) VALUES (?, ?, ?, ?, ?)",
        (farm['id'], float(temperature), 60.0, float(rainfall), forecast)
    )
    
    # Save prediction log
    inputs_json = json.dumps({
        "moisture": float(moisture),
        "temperature": float(temperature),
        "ph": float(ph),
        "nitrogen": float(nitrogen),
        "phosphorus": float(phosphorus),
        "potassium": float(potassium),
        "forecast": forecast,
        "rainfall": float(rainfall)
    })
    results_json = json.dumps(rec)
    
    cursor.execute(
        "INSERT INTO predictions (farm_id, prediction_type, inputs, results, confidence) VALUES (?, 'irrigation', ?, ?, ?)",
        (farm['id'], inputs_json, results_json, rec['confidence'])
    )
    
    db.commit()
    db.close()
    
    return jsonify(rec)

@api.route('/predict/disease', methods=['POST'])
def predict_disease():
    user_id = get_current_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
        
    crop_type = request.form.get('crop_type')
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
        
    if not crop_type:
        return jsonify({"error": "Missing crop type selection"}), 400
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        
        # Ensure directories exist
        upload_path = os.path.join(Config.UPLOAD_FOLDER, 'original_images')
        os.makedirs(upload_path, exist_ok=True)
        
        saved_file_path = os.path.join(upload_path, filename)
        file.save(saved_file_path)
        
        # Run classification mockup engine
        result = predict_crop_disease(filename, crop_type)
        
        # Record prediction in DB
        db = get_db()
        farm = db.execute("SELECT id FROM farms WHERE user_id = ?", (user_id,)).fetchone()
        if farm:
            cursor = db.cursor()
            inputs_json = json.dumps({"image_name": filename, "crop_type": crop_type})
            results_json = json.dumps(result)
            cursor.execute(
                "INSERT INTO predictions (farm_id, prediction_type, inputs, results, confidence) VALUES (?, 'disease', ?, ?, ?)",
                (farm['id'], inputs_json, results_json, result['confidence'])
            )
            db.commit()
        db.close()
        
        return jsonify(result)
        
    return jsonify({"error": "Allowed file types are png, jpg, jpeg"}), 400

@api.route('/irrigation/toggle', methods=['POST'])
def irrigation_toggle():
    user_id = get_current_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
        
    data = request.get_json() or {}
    action = data.get('action') # 'pump_on' or 'pump_off'
    water_volume = data.get('water_volume_liters', 0.0)
    duration = data.get('duration_minutes', 0)
    
    if action not in ['pump_on', 'pump_off']:
        return jsonify({"error": "Invalid action"}), 400
        
    db = get_db()
    farm = db.execute("SELECT id FROM farms WHERE user_id = ?", (user_id,)).fetchone()
    if not farm:
        db.close()
        return jsonify({"error": "No farm found"}), 404
        
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO irrigation_history (farm_id, action, water_volume_liters, duration_minutes, triggered_by) VALUES (?, ?, ?, ?, ?)",
        (farm['id'], action, float(water_volume), int(duration), 'Manual')
    )
    db.commit()
    db.close()
    
    return jsonify({"message": f"Pump successfully toggled: {action}", "status": "ON" if action == 'pump_on' else "OFF"})

@api.route('/reports/download', methods=['GET'])
def download_report():
    user_id = get_current_user()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
        
    db = get_db()
    farm = db.execute("SELECT * FROM farms WHERE user_id = ?", (user_id,)).fetchone()
    if not farm:
        db.close()
        return jsonify({"error": "No farm found"}), 404
        
    # Pull prediction logs and irrigation history
    predictions_logs = db.execute(
        "SELECT prediction_type, results, confidence, created_at FROM predictions WHERE farm_id = ? ORDER BY created_at DESC",
        (farm['id'],)
    ).fetchall()
    
    irrigation_logs = db.execute(
        "SELECT action, water_volume_liters, duration_minutes, triggered_by, timestamp FROM irrigation_history WHERE farm_id = ? ORDER BY timestamp DESC",
        (farm['id'],)
    ).fetchall()
    
    db.close()
    
    # Make a temporary report text file in the workspace directory under static or a temp folder
    report_dir = os.path.join(Config.BASE_DIR, 'reports')
    os.makedirs(report_dir, exist_ok=True)
    
    report_file_path = os.path.join(report_dir, f"farm_report_{farm['id']}.txt")
    
    with open(report_file_path, 'w') as f:
        f.write("="*50 + "\n")
        f.write(f"AGRICULTURAL HEALTH AND IRRIGATION REPORT\n")
        f.write(f"Farm Name: {farm['farm_name']}\n")
        f.write(f"Crop: {farm['crop_type']}\n")
        f.write(f"Location: {farm['location']}\n")
        f.write(f"Size: {farm['farm_size']} Acres\n")
        f.write("="*50 + "\n\n")
        
        f.write("--- IRRIGATION EVENTS LOG ---\n")
        f.write(f"{'Timestamp':20} | {'Action':8} | {'Volume (L)':10} | {'Duration (min)':14} | {'Triggered By':12}\n")
        f.write("-" * 75 + "\n")
        for log in irrigation_logs:
            f.write(f"{log['timestamp']:20} | {log['action']:8} | {log['water_volume_liters']:10.1f} | {log['duration_minutes']:14d} | {log['triggered_by']:12}\n")
            
        f.write("\n\n--- AI CLASSIFIER AND PREDICTIONS ---\n")
        f.write(f"{'Timestamp':20} | {'Type':10} | {'Confidence':10} | {'Result':30}\n")
        f.write("-" * 75 + "\n")
        for pred in predictions_logs:
            res_obj = json.loads(pred['results'])
            res_str = ""
            if pred['prediction_type'] == 'irrigation':
                res_str = f"{res_obj.get('status')}: {res_obj.get('water_volume_liters')}L"
            else:
                res_str = f"{res_obj.get('crop')} - {res_obj.get('disease')} ({res_obj.get('health_status')})"
                
            f.write(f"{pred['created_at']:20} | {pred['prediction_type']:10} | {pred['confidence']:9.1f}% | {res_str:30}\n")
            
    return send_file(report_file_path, as_attachment=True, download_name="farm_irrigation_report.txt")
