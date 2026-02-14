import subprocess
import json
import os
import sys
import time
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import io

app = Flask(__name__)
CORS(app)

def run_spydox_extractor(username):
    """Run the spydox extractor and capture both console output and file content"""
    try:
        # Clean up any previous extracted files
        if os.path.exists('extracted_urls.txt'):
            os.remove('extracted_urls.txt')
        
        # Run the spydox script with username
        result = subprocess.run(
            [sys.executable, 'spydox.py'],
            input=username + '\n',  # Send username as input since spydox.py uses input()
            capture_output=True,
            text=True,
            timeout=120  # Increased timeout for larger profiles
        )
        
        # Combine stdout and stderr
        console_output = result.stdout + result.stderr
        
        # Read the extracted URLs file if it exists
        urls_data = []
        if os.path.exists('extracted_urls.txt'):
            with open('extracted_urls.txt', 'r', encoding='utf-8') as f:
                file_content = f.read()
            
            # Parse the file to extract URLs
            urls_data = parse_urls_file('extracted_urls.txt')
        else:
            file_content = "No extracted_urls.txt file was created"
        
        return {
            "success": True,
            "console_output": console_output,
            "file_content": file_content,
            "urls_data": urls_data,
            "username": username
        }
            
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Extraction timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def parse_urls_file(filename='extracted_urls.txt'):
    """Parse the extracted_urls.txt file and return structured URL data"""
    urls_data = {
        "total_posts": 0,
        "total_images": 0,
        "posts": []
    }
    
    try:
        if not os.path.exists(filename):
            return urls_data
        
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        current_post = None
        current_images = []
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('POST ID:'):
                # Save previous post if exists
                if current_post and current_images:
                    urls_data["posts"].append({
                        "post_id": current_post,
                        "images": current_images
                    })
                    urls_data["total_posts"] += 1
                    urls_data["total_images"] += len(current_images)
                
                # Start new post
                current_post = line.replace('POST ID:', '').strip()
                current_images = []
            
            elif line.startswith('URL:'):
                url = line.replace('URL:', '').strip()
                if url and current_post:
                    current_images.append(url)
            
            elif line.startswith('  Image'):
                # Skip image numbers, we'll catch the URL in next line
                pass
        
        # Add the last post
        if current_post and current_images:
            urls_data["posts"].append({
                "post_id": current_post,
                "images": current_images
            })
            urls_data["total_posts"] += 1
            urls_data["total_images"] += len(current_images)
        
        # Also extract just the URLs in a flat list
        urls_data["all_image_urls"] = []
        for post in urls_data["posts"]:
            urls_data["all_image_urls"].extend(post["images"])
        
        return urls_data
        
    except Exception as e:
        print(f"Error parsing URLs file: {e}")
        return urls_data

def extract_image_urls_only(filename='extracted_urls.txt'):
    """Simple function to extract only the image URLs from the file"""
    image_urls = []
    
    try:
        if not os.path.exists(filename):
            return image_urls
        
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip().startswith('URL:'):
                    url = line.replace('URL:', '').strip()
                    if url and url.startswith('http'):
                        image_urls.append(url)
        
        return image_urls
        
    except Exception as e:
        print(f"Error extracting URLs: {e}")
        return image_urls

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "service": "Spydox Instagram Extractor API",
        "endpoints": {
            "/extract/<username>": "GET - Extract Instagram posts",
            "/extract": "POST - Extract Instagram posts (JSON)",
            "/download/<username>": "GET - Download as file",
            "/urls/<username>": "GET - Get only image URLs",
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

@app.route('/urls/<username>', methods=['GET'])
def get_urls_only(username):
    """Extract and return only the image URLs"""
    username = username.replace('@', '').strip()
    
    # Run the extractor
    extract_result = run_spydox_extractor(username)
    
    if extract_result.get('success'):
        # Get only the image URLs
        image_urls = extract_image_urls_only('extracted_urls.txt')
        
        return jsonify({
            "success": True,
            "username": username,
            "total_images": len(image_urls),
            "image_urls": image_urls
        })
    else:
        return jsonify(extract_result)

@app.route('/download/<username>', methods=['GET'])
def download(username):
    """Extract and download the full extracted_urls.txt file"""
    username = username.replace('@', '').strip()
    
    # Run the extractor
    extract_result = run_spydox_extractor(username)
    
    if extract_result.get('success') and os.path.exists('extracted_urls.txt'):
        return send_file(
            'extracted_urls.txt',
            as_attachment=True,
            download_name=f"instagram_{username}_urls.txt",
            mimetype='text/plain'
        )
    else:
        return jsonify({
            "success": False, 
            "error": "Failed to extract or file not found"
        })

@app.route('/cleanup', methods=['POST'])
def cleanup():
    """Clean up generated files"""
    try:
        if os.path.exists('extracted_urls.txt'):
            os.remove('extracted_urls.txt')
        return jsonify({"success": True, "message": "Cleanup completed"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
