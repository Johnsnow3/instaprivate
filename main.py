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
import shlex

app = Flask(__name__)
CORS(app)

def run_spydox_extractor(username):
    """Run spydox.py and capture the generated file from /tmp"""
    try:
        # Create a unique working directory in /tmp (writable on Vercel)
        work_dir = os.path.join('/tmp', f'spydox_{int(time.time())}')
        os.makedirs(work_dir, exist_ok=True)
        
        # Copy spydox.py to work_dir
        spydox_source = os.path.join(os.getcwd(), 'spydox.py')
        spydox_dest = os.path.join(work_dir, 'spydox.py')
        
        with open(spydox_source, 'r') as f:
            spydox_content = f.read()
        
        with open(spydox_dest, 'w') as f:
            f.write(spydox_content)
        
        # Change to working directory
        original_dir = os.getcwd()
        os.chdir(work_dir)
        
        # Run spydox.py with username input
        process = subprocess.Popen(
            [sys.executable, 'spydox.py'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Send username and wait for completion
        stdout, stderr = process.communicate(input=username + '\n', timeout=60)
        console_output = stdout + stderr
        
        # Look for the generated file
        image_urls = []
        expected_files = ['extracted_urls.txt', 'extracted_urls.txt', 'urls.txt']
        
        for filename in expected_files:
            filepath = os.path.join(work_dir, filename)
            if os.path.exists(filepath):
                print(f"Found file: {filename}")
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    image_urls = extract_image_urls(content)
                break
        
        # If file not found, try to extract from console output
        if not image_urls:
            print("File not found, extracting from console output")
            image_urls = extract_image_urls(console_output)
        
        # Clean up
        os.chdir(original_dir)
        
        # Remove working directory
        try:
            import shutil
            shutil.rmtree(work_dir)
        except:
            pass
        
        if image_urls:
            return {
                "success": True,
                "username": username,
                "image_urls": image_urls,
                "total_images": len(image_urls),
                "console_output": console_output[:500] + "..." if len(console_output) > 500 else console_output,
                "file_generated": True
            }
        else:
            return {
                "success": False,
                "error": "No image URLs found",
                "username": username,
                "console_output": console_output,
                "file_generated": False
            }
            
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Extraction timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def extract_image_urls(text):
    """Extract only image URLs from text"""
    urls = []
    
    # Pattern for Instagram image URLs (from your NASA output)
    patterns = [
        # Direct image URLs with fbcdn.net
        r'https?://[^\s]+\.fbcdn\.net[^\s]+\.(?:jpg|jpeg|png|webp)[^\s]*',
        r'URL:\s*(https?://[^\s]+\.fbcdn\.net[^\s]+)',
        r'https?://[^\s]+\.cdninstagram\.com[^\s]+',
        
        # Any URL that ends with image extensions
        r'https?://[^\s]+\.(?:jpg|jpeg|png|gif|webp)(?:[?\s]|$)',
        
        # More specific pattern for your output format
        r'URL: (https?://[^\s]+)',
    ]
    
    for pattern in patterns:
        found = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
        for url in found:
            if isinstance(url, tuple):
                url = url[0]
            url = str(url).strip()
            
            # Clean up URL (remove trailing punctuation)
            url = re.sub(r'[,\s"\']+$', '', url)
            
            # Validate URL
            if url.startswith(('http://', 'https://')) and len(url) > 10:
                if url not in urls:
                    # Filter to only include image URLs (fbcdn, cdninstagram)
                    if any(x in url for x in ['fbcdn', 'cdninstagram', '.jpg', '.jpeg', '.png']):
                        urls.append(url)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)
    
    return unique_urls

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "service": "Instagram Image Extractor",
        "endpoints": {
            "/extract/<username>": "GET - Extract images from Instagram",
            "/urls-only/<username>": "GET - Get only image URLs",
            "/download/<username>": "GET - Download URLs as file",
            "/test/<username>": "GET - Test extraction"
        }
    })

@app.route('/extract/<username>', methods=['GET'])
def extract(username):
    username = username.replace('@', '').strip()
    result = run_spydox_extractor(username)
    return jsonify(result)

@app.route('/urls-only/<username>', methods=['GET'])
def urls_only(username):
    """Return only the image URLs"""
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
    """Download image URLs as a text file"""
    username = username.replace('@', '').strip()
    result = run_spydox_extractor(username)
    
    if result.get('success'):
        urls = result.get('image_urls', [])
        
        # Create formatted output
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

@app.route('/test/<username>', methods=['GET'])
def test_extraction(username):
    """Test endpoint to debug extraction"""
    username = username.replace('@', '').strip()
    
    # Test file writing in /tmp
    test_result = {}
    try:
        test_file = '/tmp/test_write.txt'
        with open(test_file, 'w') as f:
            f.write('test')
        test_result['tmp_write'] = os.path.exists(test_file)
        if os.path.exists(test_file):
            os.remove(test_file)
    except Exception as e:
        test_result['tmp_write'] = str(e)
    
    # Run extraction
    result = run_spydox_extractor(username)
    
    return jsonify({
        "test_results": test_result,
        "extraction_result": result
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "time": time.time(),
        "tmp_writable": os.access('/tmp', os.W_OK)
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
