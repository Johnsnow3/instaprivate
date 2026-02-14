import subprocess
import json
import os
import tempfile
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/extract/<username>', methods=['GET'])
def extract(username):
    try:
        # Run the spydox script
        result = subprocess.run(
            ['python', 'spydox.py', username],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Check if output file was created
        if os.path.exists('extracted_urls.txt'):
            with open('extracted_urls.txt', 'r') as f:
                content = f.read()
            os.remove('extracted_urls.txt')
            return jsonify({"success": True, "file_content": content})
        else:
            return jsonify({
                "success": False, 
                "error": "No output",
                "stdout": result.stdout
            })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
