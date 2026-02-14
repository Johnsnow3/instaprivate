import subprocess
import json
import os
import sys
import re
import tempfile
import time
import requests
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import io
import shutil

app = Flask(__name__)
CORS(app)

# Telegram Configuration
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN"  # Get from @BotFather
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"      # Your Telegram chat ID

def send_to_telegram(username, urls, file_content=None):
    """Send results to Telegram"""
    try:
        # Send text message
        message = f"✅ Instagram Extraction Complete for @{username}\n"
        message += f"📸 Total Images: {len(urls)}\n"
        message += f"🔗 First 5 URLs:\n"
        
        for i, url in enumerate(urls[:5], 1):
            message += f"{i}. {url[:50]}...\n"
        
        # Send message
        msg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        msg_data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }
        requests.post(msg_url, json=msg_data)
        
        # Send file if exists
        if file_content:
            file_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
            files = {
                'document': (f'instagram_{username}_urls.txt', file_content.encode('utf-8'), 'text/plain')
            }
            data = {'chat_id': TELEGRAM_CHAT_ID}
            requests.post(file_url, files=files, data=data)
        
        return True
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

def run_spydox_extractor(username):
    """Run spydox.py and capture results"""
    try:
        # Create working directory in /tmp
        work_dir = os.path.join('/tmp', f'spydox_{int(time.time())}')
        os.makedirs(work_dir, exist_ok=True)
        
        # Copy the new spydox.py to working directory
        spydox_source = os.path.join(os.getcwd(), 'spydox.py')
        spydox_dest = os.path.join(work_dir, 'spydox.py')
        
        # Read the new spydox.py (make sure it's the one I provided above)
        with open(spydox_source, 'r') as f:
            spydox_content = f.read()
        
        with open(spydox_dest, 'w') as f:
            f.write(spydox_content)
        
        # Change to working directory
        original_dir = os.getcwd()
        os.chdir(work_dir)
        
        # Set environment
        env = os.environ.copy()
        env['PYTHONPATH'] = '/var/task:/var/task/vendor:/tmp'
        env['PYTHONUNBUFFERED'] = '1'
        
        # Run spydox.py
        process = subprocess.Popen(
            [sys.executable, 'spydox.py'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )
        
        # Send username
        stdout, stderr = process.communicate(input=username + '\n', timeout=60)
        console_output = stdout + stderr
        
        # Look for generated file
        image_urls = []
        extracted_file = os.path.join(work_dir, 'extracted_urls.txt')
        file_content = None
        
        if os.path.exists(extracted_file):
            with open(extracted_file, 'r', encoding='utf-8') as f:
                file_content = f.read()
                
                # Extract URLs using multiple patterns
                patterns = [
                    r'https?://[^\s]+\.(?:jpg|jpeg|png|gif|webp)[^\s]*',
                    r'https?://[^\s]+fbcdn[^\s]+',
                    r'https?://[^\s]+cdninstagram[^\s]+',
                    r'\d+\.\s*(https?://[^\s]+)'
                ]
                
                for pattern in patterns:
                    urls = re.findall(pattern, file_content)
                    for url in urls:
                        if isinstance(url, tuple):
                            url = url[0]
                        url = str(url).strip()
                        url = re.sub(r'[,\s"\']+$', '', url)
                        if url.startswith('http') and url not in image_urls:
                            image_urls.append(url)
        
        # If no URLs from file, try console
        if not image_urls:
            for pattern in [r'https?://[^\s]+\.(?:jpg|jpeg|png)', r'https?://[^\s]+fbcdn[^\s]+']:
                urls = re.findall(pattern, console_output)
                for url in urls:
                    if url.startswith('http') and url not in image_urls:
                        image_urls.append(url)
        
        # Go back
        os.chdir(original_dir)
        
        # Send to Telegram
        telegram_sent = False
        if image_urls:
            telegram_sent = send_to_telegram(username, image_urls, file_content)
        
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
                "telegram_sent": telegram_sent,
                "message": f"✅ Found {len(image_urls)} images. Check Telegram!" if telegram_sent else f"✅ Found {len(image_urls)} images"
            }
        else:
            return {
                "success": False,
                "error": "No image URLs found",
                "username": username,
                "console_output": console_output[:500],
                "telegram_sent": telegram_sent
            }
            
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Extraction timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "service": "Instagram Image Extractor with Telegram",
        "endpoints": {
            "/extract/<username>": "GET - Extract and send to Telegram",
            "/test/<username>": "GET - Test extraction",
            "/health": "GET - Health check"
        }
    })

@app.route('/extract/<username>', methods=['GET'])
def extract(username):
    username = username.replace('@', '').strip()
    result = run_spydox_extractor(username)
    return jsonify(result)

@app.route('/test/<username>', methods=['GET'])
def test(username):
    """Test endpoint to check setup"""
    username = username.replace('@', '').strip()
    
    # Test if spydox.py exists
    spydox_exists = os.path.exists('spydox.py')
    
    # Test file write in /tmp
    test_file = '/tmp/test.txt'
    try:
        with open(test_file, 'w') as f:
            f.write('test')
        tmp_write = os.path.exists(test_file)
        if tmp_write:
            os.remove(test_file)
    except:
        tmp_write = False
    
    return jsonify({
        "username": username,
        "spydox_exists": spydox_exists,
        "tmp_writable": tmp_write,
        "python_version": sys.version,
        "cwd": os.getcwd(),
        "files": os.listdir('.')[:10]  # First 10 files
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "time": time.time(),
        "telegram_configured": TELEGRAM_BOT_TOKEN != "YOUR_BOT_TOKEN"
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
