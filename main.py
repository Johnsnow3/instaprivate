import subprocess
import json
import os
import sys
import re
import tempfile
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import io

app = Flask(__name__)
CORS(app)

def run_spydox_extractor(username):
    """Run the spydox extractor and capture output directly"""
    try:
        # Create a temporary directory in /tmp (writable on Vercel)
        temp_dir = tempfile.mkdtemp()
        original_dir = os.getcwd()
        
        # Change to temp directory to isolate file writes
        os.chdir(temp_dir)
        
        # Run the spydox script with username as input
        process = subprocess.Popen(
            [sys.executable, os.path.join(original_dir, 'spydox.py')],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Send username as input
        stdout, stderr = process.communicate(input=username + '\n', timeout=60)
        
        # Capture console output
        console_output = stdout + stderr
        
        # Check if extracted_urls.txt was created in temp directory
        extracted_file = os.path.join(temp_dir, 'extracted_urls.txt')
        image_urls = []
        
        if os.path.exists(extracted_file):
            # Read the file content
            with open(extracted_file, 'r', encoding='utf-8') as f:
                file_content = f.read()
            
            # Extract URLs from file content
            image_urls = extract_urls_from_text(file_content)
            
            # Also try to extract from console output as backup
            if not image_urls:
                image_urls = extract_urls_from_text(console_output)
            
            # Clean up
            os.remove(extracted_file)
        
        # If no URLs found in file, try console output
        if not image_urls:
            image_urls = extract_urls_from_text(console_output)
        
        # Change back to original directory
        os.chdir(original_dir)
        
        # Clean up temp directory
        try:
            os.rmdir(temp_dir)
        except:
            pass
        
        return {
            "success": True,
            "username": username,
            "console_output": console_output[:1000] + "..." if len(console_output) > 1000 else console_output,
            "image_urls": image_urls,
            "total_images": len(image_urls),
            "file_generated": os.path.exists(extracted_file) if 'extracted_file' in locals() else False,
            "method": "direct_extraction"
        }
            
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Extraction timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def extract_urls_from_text(text):
    """Extract image URLs from text content"""
    urls = []
    
    # URL patterns for Instagram images
    patterns = [
        # Direct image URLs
        r'https?://[^\s]+\.(?:jpg|jpeg|png|gif|webp)[^\s]*',
        r'https?://[^\s]*(?:instagram|cdninstagram|fbcdn)[^\s]*\.(?:jpg|jpeg|png|gif|webp)[^\s]*',
        
        # URLs in the format "URL: https://..."
        r'URL:\s*(https?://[^\s]+)',
        
        # Instagram post URLs
        r'https?://(?:www\.)?instagram\.com/p/[A-Za-z0-9_-]+',
        
        # Any http/https URL that might be an image
        r'(https?://[^\s]+(?:jpg|jpeg|png|gif|webp)[^\s]*)',
        r'(https?://[^\s]+media[^\s]+)',
    ]
    
    for pattern in patterns:
        found = re.findall(pattern, text, re.IGNORECASE)
        for url in found:
            # Clean up URL
            if isinstance(url, tuple):
                url = url[0]  # Take first group if multiple
            url = re.sub(r'[,\s"\']+$', '', str(url))
            
            # Validate URL
            if url.startswith(('http://', 'https://')) and len(url) > 10:
                if url not in urls:  # Avoid duplicates
                    urls.append(url)
    
    return urls

@app.route('/debug/vercel', methods=['GET'])
def debug_vercel():
    """Debug endpoint to check Vercel environment"""
    import tempfile
    
    # Test file writing
    test_results = {}
    
    # Test 1: Write to current directory
    try:
        with open('test.txt', 'w') as f:
            f.write('test')
        test_results['current_dir'] = os.path.exists('test.txt')
        if os.path.exists('test.txt'):
            os.remove('test.txt')
    except:
        test_results['current_dir'] = False
    
    # Test 2: Write to /tmp
    try:
        tmp_file = '/tmp/test.txt'
        with open(tmp_file, 'w') as f:
            f.write('test')
        test_results['tmp_dir'] = os.path.exists(tmp_file)
        if os.path.exists(tmp_file):
            os.remove(tmp_file)
    except:
        test_results['tmp_dir'] = False
    
    # Test 3: Use tempfile
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write('test')
            temp_name = f.name
        test_results['tempfile'] = os.path.exists(temp_name)
        if os.path.exists(temp_name):
            os.remove(temp_name)
    except:
        test_results['tempfile'] = False
    
    return jsonify({
        "environment": "Vercel" if os.environ.get('VERCEL') else "Local",
        "current_dir": os.getcwd(),
        "writable_tests": test_results,
        "temp_dir": tempfile.gettempdir()
    })

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

@app.route('/urls-only/<username>', methods=['GET'])
def urls_only(username):
    """Get only the image URLs"""
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
    """Download URLs as file"""
    username = username.replace('@', '').strip()
    result = run_spydox_extractor(username)
    
    if result.get('success'):
        urls = result.get('image_urls', [])
        
        # Create formatted output
        output = f"Instagram Image URLs for @{username}\n"
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
            download_name=f"instagram_{username}_urls.txt",
            mimetype='text/plain'
        )
    else:
        return jsonify(result)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy", 
        "time": __import__('time').time(),
        "environment": "Vercel" if os.environ.get('VERCEL') else "Local"
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
