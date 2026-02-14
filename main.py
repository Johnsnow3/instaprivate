import subprocess
import json
import os
import sys
import re
import tempfile
import time
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = ""  # Get from @BotFather
TELEGRAM_CHAT_ID = ""      # Your Telegram chat ID

def send_to_telegram(message, file_content=None):
    """Send message or file to Telegram"""
    try:
        if file_content:
            # Send as file
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
            files = {'document': ('extracted_urls.txt', file_content.encode('utf-8'))}
            data = {'chat_id': TELEGRAM_CHAT_ID}
            response = requests.post(url, files=files, data=data)
        else:
            # Send as message
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
            response = requests.post(url, json=data)
        
        return response.ok
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

def run_spydox_with_telegram(username):
    """Run spydox.py and send results via Telegram"""
    try:
        # Create temp directory
        work_dir = tempfile.mkdtemp()
        original_dir = os.getcwd()
        
        # Copy spydox.py
        with open('spydox.py', 'r') as f:
            spydox_content = f.read()
        
        with open(os.path.join(work_dir, 'spydox.py'), 'w') as f:
            f.write(spydox_content)
        
        os.chdir(work_dir)
        
        # Run spydox
        process = subprocess.Popen(
            [sys.executable, 'spydox.py'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate(input=username + '\n', timeout=60)
        
        # Check for generated file
        file_content = None
        for filename in ['extracted_urls.txt', 'urls.txt']:
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    file_content = f.read()
                break
        
        # Send to Telegram
        telegram_status = False
        if file_content:
            # Send file to Telegram
            telegram_status = send_to_telegram(
                f"Instagram extraction for @{username} completed!",
                file_content
            )
            
            # Extract URLs for API response
            urls = extract_image_urls(file_content)
        else:
            # Send console output to Telegram
            telegram_status = send_to_telegram(
                f"Instagram extraction for @{username}\n\nSTDOUT:\n{stdout[:1000]}\n\nSTDERR:\n{stderr[:500]}"
            )
            urls = extract_image_urls(stdout + stderr)
        
        os.chdir(original_dir)
        
        return {
            "success": len(urls) > 0,
            "username": username,
            "image_urls": urls,
            "total_images": len(urls),
            "telegram_sent": telegram_status,
            "message": f"Results sent to Telegram. Check your bot!"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def extract_image_urls(text):
    """Extract image URLs (same as above)"""
    urls = []
    patterns = [
        r'https?://[^\s]+\.fbcdn\.net[^\s]+\.(?:jpg|jpeg|png|webp)[^\s]*',
        r'URL:\s*(https?://[^\s]+\.fbcdn\.net[^\s]+)',
        r'https?://[^\s]+\.cdninstagram\.com[^\s]+',
        r'https?://[^\s]+\.(?:jpg|jpeg|png|gif|webp)(?:[?\s]|$)',
    ]
    
    for pattern in patterns:
        found = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
        for url in found:
            if isinstance(url, tuple):
                url = url[0]
            url = str(url).strip()
            url = re.sub(r'[,\s"\']+$', '', url)
            
            if url.startswith(('http://', 'https://')) and len(url) > 10:
                if url not in urls and any(x in url for x in ['fbcdn', 'cdninstagram']):
                    urls.append(url)
    
    return list(dict.fromkeys(urls))  # Remove duplicates

@app.route('/telegram/<username>', methods=['GET'])
def extract_with_telegram(username):
    """Extract and send to Telegram"""
    username = username.replace('@', '').strip()
    result = run_spydox_with_telegram(username)
    return jsonify(result)

@app.route('/extract/<username>', methods=['GET'])
def extract(username):
    """Standard extraction"""
    username = username.replace('@', '').strip()
    
    # Use the first option's function here
    from your_first_option import run_spydox_extractor
    result = run_spydox_extractor(username)
    return jsonify(result)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
