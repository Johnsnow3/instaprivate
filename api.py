# api.py - API wrapper for the Spydox extractor
import subprocess
import json
import os
import tempfile
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def run_extractor(username):
    """Run the extractor script and capture output"""
    try:
        # Create temporary file for output
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as tmp:
            output_file = tmp.name
        
        # Run the extractor script (save the original as extractor.py)
        result = subprocess.run(
            ['python', 'extractor.py', username],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Check if the output file was created
        if os.path.exists('extracted_urls.txt'):
            with open('extracted_urls.txt', 'r') as f:
                content = f.read()
            os.remove('extracted_urls.txt')
            
            return {
                "success": True,
                "username": username,
                "file_content": content,
                "logs": result.stdout
            }
        else:
            return {
                "success": False,
                "error": "No output file generated",
                "stdout": result.stdout,
                "stderr": result.stderr
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
        "usage": "GET /extract/<username>"
    })

@app.route('/extract/<username>', methods=['GET'])
def extract(username):
    result = run_extractor(username)
    return jsonify(result)

@app.route('/extract', methods=['POST'])
def extract_post():
    data = request.get_json()
    if not data or 'username' not in data:
        return jsonify({"success": False, "error": "Username required"}), 400
    
    username = data['username'].replace('@', '').strip()
    result = run_extractor(username)
    return jsonify(result)

@app.route('/download/<username>', methods=['GET'])
def download(username):
    """Run extraction and return file directly"""
    result = run_extractor(username)
    
    if result.get('success'):
        content = result.get('file_content', '')
        from io import BytesIO
        file_obj = BytesIO()
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
    app.run(host='0.0.0.0', port=port, debug=False)
