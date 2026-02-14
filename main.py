import subprocess
import json
import os
import sys
import re
import time
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import io

app = Flask(__name__)
CORS(app)

def extract_image_urls_from_file(filename='extracted_urls.txt'):
    """Extract only image URLs from the extracted_urls.txt file"""
    image_urls = []
    
    if not os.path.exists(filename):
        return []
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Regular expression to find URLs (both http and https)
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        
        # Find all URLs in the file
        all_urls = re.findall(url_pattern, content)
        
        # Filter for image URLs (common image extensions and CDN patterns)
        image_patterns = [
            r'\.(jpg|jpeg|png|gif|bmp|webp)(\?|$)',
            r'cdninstagram\.com',
            r'fbcdn\.net',
            r'instagram\.f.*\.fbcdn\.net'
        ]
        
        for url in all_urls:
            for pattern in image_patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    if url not in image_urls:  # Avoid duplicates
                        image_urls.append(url)
                    break
        
        return image_urls
    
    except Exception as e:
        print(f"Error reading file: {e}")
        return []

def run_spydox_extractor(username):
    """Run the spydox extractor and capture output"""
    try:
        # Clean up any previous extracted_urls.txt
        if os.path.exists('extracted_urls.txt'):
            os.remove('extracted_urls.txt')
        
        # Run the spydox script with username
        # Note: spydox.py expects interactive input, so we need to provide it
        process = subprocess.Popen(
            [sys.executable, 'spydox.py'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Send username as input and get output
        stdout, stderr = process.communicate(input=f"{username}\n", timeout=60)
        
        # Combine stdout and stderr
        output = stdout + stderr
        
        # Wait a moment for file to be written
        time.sleep(2)
        
        # Extract image URLs from the generated file
        image_urls = extract_image_urls_from_file('extracted_urls.txt')
        
        # Also try to extract URLs from stdout if file doesn't exist
        if not image_urls:
            url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
            all_urls = re.findall(url_pattern, output)
            image_patterns = [r'\.(jpg|jpeg|png|gif|webp)', r'cdninstagram', r'fbcdn']
            
            for url in all_urls:
                for pattern in image_patterns:
                    if re.search(pattern, url, re.IGNORECASE):
                        if url not in image_urls:
                            image_urls.append(url)
                        break
        
        return {
            "success": True,
            "console_output": output,
            "image_urls": image_urls,
            "total_images": len(image_urls),
            "username": username
        }
            
    except subprocess.TimeoutExpired:
        process.kill()
        return {"success": False, "error": "Extraction timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "service": "Spydox Instagram Extractor API",
        "endpoints": {
            "/extract/<username>": "GET - Extract Instagram posts and get image URLs",
            "/extract": "POST - Extract Instagram posts (JSON with username field)",
            "/download/<username>": "GET - Download full report as file",
            "/images/<username>": "GET - Get only image URLs",
            "/health": "GET - Health check"
        }
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "time": time.time()})

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

@app.route('/images/<username>', methods=['GET'])
def get_images_only(username):
    """Extract and return only image URLs"""
    username = username.replace('@', '').strip()
    result = run_spydox_extractor(username)
    
    if result.get('success'):
        return jsonify({
            "success": True,
            "username": username,
            "total_images": result.get('total_images', 0),
            "image_urls": result.get('image_urls', [])
        })
    else:
        return jsonify(result)

@app.route('/download/<username>', methods=['GET'])
def download(username):
    """Extract and download full report as file"""
    username = username.replace('@', '').strip()
    result = run_spydox_extractor(username)
    
    if result.get('success'):
        # Create a comprehensive report
        report = f"""Instagram Extraction Report for @{username}
{'='*60}

Total Images Found: {result.get('total_images', 0)}

{'='*60}
IMAGE URLs:
{'='*60}

"""
        # Add all image URLs
        for i, url in enumerate(result.get('image_urls', []), 1):
            report += f"{i}. {url}\n"
        
        report += f"\n{'='*60}\nFull Console Output:\n{'='*60}\n\n"
        report += result.get('console_output', '')
        
        file_obj = io.BytesIO()
        file_obj.write(report.encode('utf-8'))
        file_obj.seek(0)
        
        return send_file(
            file_obj,
            as_attachment=True,
            download_name=f"instagram_{username}_report.txt",
            mimetype='text/plain'
        )
    else:
        return jsonify(result)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
