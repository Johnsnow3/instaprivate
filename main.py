import subprocess
import json
import os
import sys
import re
import tempfile
import time
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import io
import shutil

app = Flask(__name__)
CORS(app)

def run_spydox_extractor(username):
    """Run spydox.py and capture the generated file"""
    try:
        # Create working directory in /tmp
        work_dir = os.path.join('/tmp', f'spydox_{int(time.time())}')
        os.makedirs(work_dir, exist_ok=True)
        
        # Copy spydox.py to working directory
        spydox_source = os.path.join(os.getcwd(), 'spydox.py')
        spydox_dest = os.path.join(work_dir, 'spydox.py')
        
        with open(spydox_source, 'r') as f:
            spydox_content = f.read()
        
        with open(spydox_dest, 'w') as f:
            f.write(spydox_content)
        
        # Change to working directory
        original_dir = os.getcwd()
        os.chdir(work_dir)
        
        # Set environment to find installed packages
        env = os.environ.copy()
        env['PYTHONPATH'] = '/var/task:/var/task/vendor:/tmp'
        
        # Run spydox.py
        process = subprocess.Popen(
            [sys.executable, 'spydox.py'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )
        
        # Send username and wait
        stdout, stderr = process.communicate(input=username + '\n', timeout=60)
        console_output = stdout + stderr
        
        # Look for generated file
        image_urls = []
        extracted_file = os.path.join(work_dir, 'extracted_urls.txt')
        
        if os.path.exists(extracted_file):
            with open(extracted_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Extract URLs using regex
                urls = re.findall(r'https?://[^\s]+\.(?:jpg|jpeg|png|gif|webp)[^\s]*', content)
                if not urls:
                    urls = re.findall(r'URL:\s*(https?://[^\s]+)', content)
                if not urls:
                    urls = re.findall(r'https?://[^\s]+fbcdn[^\s]+', content)
                
                # Clean URLs
                for url in urls:
                    if isinstance(url, tuple):
                        url = url[0]
                    url = str(url).strip()
                    url = re.sub(r'[,\s"\']+$', '', url)
                    if url.startswith('http') and url not in image_urls:
                        image_urls.append(url)
        
        # If no file, try to extract from console
        if not image_urls:
            urls = re.findall(r'https?://[^\s]+\.(?:jpg|jpeg|png|gif|webp)[^\s]*', console_output)
            for url in urls:
                if url.startswith('http') and url not in image_urls:
                    image_urls.append(url)
        
        # Go back
        os.chdir(original_dir)
        
        # Clean up
        try:
            shutil.rmtree(work_dir)
        except:
            pass
        
        if image_urls:
            return {
                "success": True,
                "username": username,
                "image_urls": image_urls,
                "total_images": len(image_urls),
                "console_output": console_output[:500] + "..." if len(console_output) > 500 else console_output
            }
        else:
            return {
                "success": False,
                "error": "No image URLs found",
                "username": username,
                "console_output": console_output
            }
            
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Extraction timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "service": "Instagram Image Extractor",
        "endpoints": {
            "/extract/<username>": "GET - Extract images",
            "/urls-only/<username>": "GET - Get only URLs",
            "/download/<username>": "GET - Download as file",
            "/health": "GET - Health check"
        }
    })

@app.route('/extract/<username>', methods=['GET'])
def extract(username):
    username = username.replace('@', '').strip()
    result = run_spydox_extractor(username)
    return jsonify(result)

@app.route('/urls-only/<username>', methods=['GET'])
def urls_only(username):
    username = username.replace('@', '').strip()
    result = run_spydox_extractor(username)
    
    if result.get('success'):
        return jsonify({
            "success": True,
            "username": username,
            "urls": result.get('image_urls', []),
            "count": result.get('total_images', 0)
        })
    else:
        return jsonify(result)

@app.route('/download/<username>', methods=['GET'])
def download(username):
    username = username.replace('@', '').strip()
    result = run_spydox_extractor(username)
    
    if result.get('success'):
        urls = result.get('image_urls', [])
        
        output = f"Instagram Images for @{username}\n"
        output += "=" * 60 + "\n"
        output += f"Total Images: {len(urls)}\n"
        output += "=" * 60 + "\n\n"
        
        for i, url in enumerate(urls, 1):
            output += f"{i}. {url}\n"
        
        file_obj = io.BytesIO()
        file_obj.write(output.encode('utf-8'))
        file_obj.seek(0)
        
        return send_file(
            file_obj,
            as_attachment=True,
            download_name=f"instagram_{username}_images.txt",
            mimetype='text/plain'
        )
    else:
        return jsonify(result)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "time": time.time(),
        "python_version": sys.version
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
