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
    """Run the spydox extractor with fallback methods"""
    try:
        # Try multiple methods to get images
        
        # Method 1: Run the original spydox.py
        result = method1_original_spydox(username)
        if result.get('success') and result.get('image_urls'):
            return result
            
        # Method 2: Try direct Instagram scraping
        result = method2_direct_scrape(username)
        if result.get('success') and result.get('image_urls'):
            return result
            
        # Method 3: Return error with suggestions
        return {
            "success": False,
            "error": "Could not extract images. Instagram may have changed their structure.",
            "username": username,
            "suggestion": "Try using instagram-scraper or instaloader library instead",
            "console_output": result.get('console_output', 'No output')
        }
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def method1_original_spydox(username):
    """Try the original spydox method"""
    try:
        temp_dir = tempfile.mkdtemp()
        original_dir = os.getcwd()
        os.chdir(temp_dir)
        
        process = subprocess.Popen(
            [sys.executable, os.path.join(original_dir, 'spydox.py')],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate(input=username + '\n', timeout=30)
        console_output = stdout + stderr
        
        # Check for file
        image_urls = []
        extracted_file = os.path.join(temp_dir, 'extracted_urls.txt')
        
        if os.path.exists(extracted_file):
            with open(extracted_file, 'r') as f:
                content = f.read()
                image_urls = extract_urls_from_text(content)
            os.remove(extracted_file)
        
        os.chdir(original_dir)
        
        return {
            "success": len(image_urls) > 0,
            "username": username,
            "image_urls": image_urls,
            "total_images": len(image_urls),
            "console_output": console_output[:500],
            "method": "original_spydox"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def method2_direct_scrape(username):
    """Alternative method using requests directly"""
    import requests
    from bs4 import BeautifulSoup
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        url = f'https://www.instagram.com/{username}/'
        response = requests.get(url, headers=headers, timeout=10)
        
        # Extract from response text
        image_urls = extract_urls_from_text(response.text)
        
        # Also look for JSON data
        soup = BeautifulSoup(response.text, 'html.parser')
        scripts = soup.find_all('script', type='application/json')
        
        for script in scripts:
            if script.string:
                urls = extract_urls_from_text(script.string)
                image_urls.extend(urls)
        
        # Remove duplicates
        image_urls = list(set(image_urls))
        
        return {
            "success": len(image_urls) > 0,
            "username": username,
            "image_urls": image_urls,
            "total_images": len(image_urls),
            "method": "direct_scrape"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def extract_urls_from_text(text):
    """Extract image URLs from text"""
    urls = []
    patterns = [
        r'https?://[^\s]+\.(?:jpg|jpeg|png|gif|webp)[^\s]*',
        r'https?://[^\s]*(?:instagram|cdninstagram|fbcdn)[^\s]*\.(?:jpg|jpeg|png|gif|webp)',
        r'https?://[^\s]+/p/[A-Za-z0-9_-]+',
        r'"display_url":"([^"]+)"',
        r'"display_src":"([^"]+)"',
        r'"url":"([^"]+\.(?:jpg|jpeg|png))"',
    ]
    
    for pattern in patterns:
        found = re.findall(pattern, text, re.IGNORECASE)
        for url in found:
            if isinstance(url, tuple):
                url = url[0]
            url = str(url).replace('\\u0026', '&').strip()
            if url.startswith(('http://', 'https://')) and len(url) > 10:
                if url not in urls:
                    urls.append(url)
    
    return urls

@app.route('/extract/<username>', methods=['GET'])
def extract(username):
    username = username.replace('@', '').strip()
    result = run_spydox_extractor(username)
    return jsonify(result)

@app.route('/debug/test', methods=['GET'])
def debug_test():
    """Test endpoint to check if Instagram is accessible"""
    import requests
    try:
        response = requests.get('https://www.instagram.com', timeout=5)
        return jsonify({
            "instagram_accessible": response.status_code == 200,
            "status_code": response.status_code
        })
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
