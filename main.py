import subprocess
import json
import os
import sys
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import io

app = Flask(__name__)
CORS(app)

def run_spydox_extractor(username):
    """Run the spydox extractor and capture output"""
    try:
        # Run the spydox script with username
        result = subprocess.run(
            [sys.executable, 'spydox.py', username],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Combine stdout and stderr
        output = result.stdout + result.stderr
        
        return {
            "success": True,
            "file_content": output,
            "username": username
        }
            
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Extraction timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "service": "Spydox Instagram Extractor API",
        "endpoints": {
            "/extract/<username>": "GET - Extract Instagram posts",
            "/health": "GET - Health check"
        }
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "time": __import__('time').time()})

@app.route('/extract/<username>', methods=['GET'])
def extract(username):
    username = username.replace('@', '').strip()
    result = run_spydox_extractor(username)
    return jsonify(result)

@app.route('/extract', methods=['POST'])
def extract_post():
    data = request.get_json()
    if not data or 'username' not in data:
        return jsonify({"success": False, "error": "Username required"}), 400
    
    username = data['username'].replace('@', '').strip()
    result = run_spydox_extractor(username)
    return jsonify(result)

@app.route('/download/<username>', methods=['GET'])
def download(username):
    """Extract and download as file"""
    username = username.replace('@', '').strip()
    result = run_spydox_extractor(username)
    
    if result.get('success'):
        content = result.get('file_content', '')
        file_obj = io.BytesIO()
        file_obj.write(content.encode('utf-8'))
        file_obj.seek(0)
        
        return send_file(
            file_obj,
            as_attachment=True,
            download_name=f"instagram_{username}.txt",
            mimetype='text/plain'
        )
    else:
        return jsonify(result)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
