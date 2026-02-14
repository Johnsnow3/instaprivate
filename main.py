import subprocess
import json
import os
import tempfile
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import io
import sys

app = Flask(__name__)
CORS(app)

def run_spydox_extractor(username):
    """Run the spydox extractor and capture output"""
    try:
        # Create a temporary file for output
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as tmp:
            output_file = tmp.name
        
        # Run the spydox script with username
        result = subprocess.run(
            [sys.executable, 'spydox.py', username],
            capture_output=True,
            text=True,
            timeout=60,
            env={**os.environ, 'PYTHONUNBUFFERED': '1'}
        )
        
        print(f"[*] stdout: {result.stdout}")
        print(f"[*] stderr: {result.stderr}")
        
        # Check if the script created extracted_urls.txt
        if os.path.exists('extracted_urls.txt'):
            with open('extracted_urls.txt', 'r') as f:
                content = f.read()
            os.remove('extracted_urls.txt')
            return {"success": True, "file_content": content}
        
        # Check if any output file was created
        for file in os.listdir('.'):
            if file.endswith('.txt') and 'extracted' in file:
                with open(file, 'r') as f:
                    content = f.read()
                os.remove(file)
                return {"success": True, "file_content": content}
        
        # If no file, return the stdout
        if result.stdout:
            return {"success": True, "file_content": result.stdout}
        else:
            return {"success": False, "error": "No output generated", "stderr": result.stderr}
            
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
    port = int(os.environ.get('PORT', 8080))
    print(f"[+] Starting Spydox API on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
