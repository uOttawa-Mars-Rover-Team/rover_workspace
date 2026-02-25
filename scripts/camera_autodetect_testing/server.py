import signal
import os
import atexit
import time
import threading
from flask import Flask, jsonify, request
from flask_cors import CORS

from autostartcams import (
    CameraManager,
    ImageMonitor,
    get_connected_cameras,
    sanitize_name_for_ros,
)

app = Flask(__name__)
CORS(app)

monitor = None
manager = None

def initialize_camera_system():
    global monitor, manager
    print("Starting camera management system...")

    # Dummy monitor (required for compatibility)
    monitor = ImageMonitor()
    
    # Initialize Manager
    manager = CameraManager(monitor)
    
    camera_thread = threading.Thread(target=manager.start, daemon=True)
    camera_thread.start()
    
    print("✓ RTSP Server running in background")

def get_camera_status():
    if manager is None: return []
    cameras_status = []

    # Safely access cameras dictionary
    try:
        current_cameras = dict(manager.cameras)
    except:
        return []

    for symlink, cam in current_cameras.items():
        uptime = time.monotonic() - cam['startup_time']
        
        status = "active"

        camera_info = {
            "symlink_name": cam['device'],
            "camera_name": cam['camera_name'],
            "status": status,
            "uptime": round(uptime, 1),
            "rtsp_url": f"rtsp://<JETSON_IP>:8554{symlink}",
            "process_id": os.getpid()
        }
        cameras_status.append(camera_info)
    
    return cameras_status

def cleanup_camera_system(*args):
    global manager
    if manager:
        manager.stop()

# ==================== API ENDPOINTS ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "ok", 
        "manager_active": manager is not None,
        "mode": "Pure RTSP (No ROS)"
    }), 200

@app.route('/api/cameras', methods=['GET'])
def get_cameras():
    if manager is None: return jsonify({"status": "error", "message": "Starting up..."}), 503
    return jsonify({"status": "success", "cameras": get_camera_status()}), 200

@app.route('/api/cameras/connected', methods=['GET'])
def get_connected():
    return jsonify({"status": "success", "cameras": get_connected_cameras()}), 200

@app.route('/api/cameras/<camera_identifier>/restart', methods=['POST'])
def restart_camera(camera_identifier):
    if manager is None: return jsonify({"error": "Not started"}), 503
    manager.restart_camera(camera_identifier)
    return jsonify({"status": "success", "message": f"Restart triggered for {camera_identifier}"}), 200

@app.route('/api/cameras/add/<path:symlink_name>', methods=['POST'])
def add_camera(symlink_name):
    if manager is None: return jsonify({"error": "Not started"}), 503
    full_path = symlink_name if symlink_name.startswith("/") else f"/dev/v4l/by-id/{symlink_name}"
    manager.add_camera(full_path)
    return jsonify({"status": "success", "message": f"Added {full_path}"}), 201

if __name__ == '__main__':
    atexit.register(cleanup_camera_system)
    
    # 1. Start the RTSP Server (Background)
    initialize_camera_system()
    
    # 2. Start the Flask API (Foreground)
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False, threaded=True)