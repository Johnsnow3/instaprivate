import subprocess
import json
import os
import sys
import time
import re
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import io

app = Flask(__name__)
CORS(app)

def run_spydox_extractor(username):
    """Run the spydox extractor and capture the extracted_urls.txt file"""
    try:
        # Clean up any existing extracted_urls.txt file
        if os.path.exists('extracted_urls.txt'):
            os.remove('extracted_urls.txt')
        
        # Run the spydox script with username (it will generate extracted_urls.txt)
        result = subprocess.run(
            [sys.executable, 'spydox.py'],
            input=username + '\n',  # Send username as input
            capture_output=True,
            text=True,
            timeout=120  # Increased timeout for larger accounts
        )
        
        # Wait a moment for file to be written
        time.sleep(1)
        
        # Check if extracted_urls.txt was created
        if os.path.exists('extracted_urls.txt'):
            # Read and parse the extracted_urls.txt file
            image_urls = parse_extracted_urls_file('extracted_urls.txt')
            
            # Also get console output
            console_output = result.stdout + result.stderr
            
            return {
                "success": True,
                "username": username,
                "console_output": console_output,
                "image_urls": image_urls,
                "total_images": len(image_urls),
                "file_generated": True
            }
        else:
            return {
                "success": False,
                "error": "extracted_urls.txt was not generated",
                "console_output": result.stdout + result.stderr,
                "username": username
            }
            
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Extraction timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def parse_extracted_urls_file(filename):
    """Parse the extracted_urls.txt file and extract only image URLs"""
    image_urls = []
    
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            content = file.read()
            
            # Method 1: Extract URLs using regex pattern for Instagram image URLs
            # Instagram image URLs typically contain these patterns
            url_patterns = [
                r'https?://[^\s]+\.(?:jpg|jpeg|png|gif|webp)[^\s]*',
                r'https?://[^\s]+instagram[^\s]+/p/[^\s]+',
                r'https?://[^\s]+cdninstagram[^\s]+',
                r'https?://[^\s]+fbcdn[^\s]+',
                r'URL:\s*(https?://[^\s]+)',
                r'(https?://[^\s]+\.(?:jpg|jpeg|png|gif|webp))',
            ]
            
            # Try each pattern
            for pattern in url_patterns:
                found_urls = re.findall(pattern, content, re.IGNORECASE)
                if found_urls:
                    # Clean and validate URLs
                    for url in found_urls:
                        # Remove trailing punctuation if any
                        url = re.sub(r'[,\s]+$', '', url)
                        if url.startswith(('http://', 'https://')) and len(url) > 10:
                            if url not in image_urls:  # Avoid duplicates
                                image_urls.append(url)
            
            # Method 2: Parse line by line looking for URLs
            lines = content.split('\n')
            for line in lines:
                # Look for lines containing URL or http
                if 'URL:' in line or 'http' in line.lower():
                    # Extract URL from line
                    url_match = re.search(r'(https?://[^\s]+)', line)
                    if url_match:
                        url = url_match.group(1)
                        # Clean up URL
                        url = re.sub(r'[,\s]+$', '', url)
                        if url.startswith(('http://', 'https://')):
                            if url not in image_urls:
                                image_urls.append(url)
            
            # Method 3: Parse structured format
            posts_data = []
            current_post = {}
            reading_urls = False
            
            for line in lines:
                if line.startswith('POST ID:'):
                    if current_post:
                        posts_data.append(current_post)
                    current_post = {'post_id': line.replace('POST ID:', '').strip(), 'images': []}
                elif line.startswith('  Image'):
                    reading_urls = True
                elif reading_urls and 'URL:' in line:
                    url_match = re.search(r'URL:\s*(https?://[^\s]+)', line)
                    if url_match:
                        url = url_match.group(1)
                        if url not in image_urls:
                            image_urls.append(url)
                        if current_post:
                            current_post['images'].append(url)
            
            # Add last post
            if current_post:
                posts_data.append(current_post)
            
            return {
                'all_urls': image_urls,
                'by_post': posts_data,
                'total': len(image_urls),
                'total_posts': len(posts_data) if posts_data else 0
            }
            
    except FileNotFoundError:
        return {'all_urls': [], 'by_post': [], 'total': 0, 'error': 'File not found'}
    except Exception as e:
        return {'all_urls': [], 'by_post': [], 'total': 0, 'error': str(e)}

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "service": "Spydox Instagram Extractor API",
        "endpoints": {
            "/extract/<username>": "GET - Extract Instagram posts and get image URLs",
            "/extract": "POST - Extract Instagram posts (JSON with username)",
            "/download/<username>": "GET - Download extracted URLs as file",
            "/urls-only/<username>": "GET - Get only image URLs",
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

@app.route('/urls-only/<username>', methods=['GET'])
def get_urls_only(username):
    """Get only the image URLs without additional data"""
    username = username.replace('@', '').strip()
    result = run_spydox_extractor(username)
    
    if result.get('success'):
        return jsonify({
            "success": True,
            "username": username,
            "urls": result.get('image_urls', {}).get('all_urls', []),
            "count": result.get('total_images', 0)
        })
    else:
        return jsonify(result)

@app.route('/download/<username>', methods=['GET'])
def download(username):
    """Download extracted URLs as file"""
    username = username.replace('@', '').strip()
    result = run_spydox_extractor(username)
    
    if result.get('success'):
        urls_data = result.get('image_urls', {})
        all_urls = urls_data.get('all_urls', [])
        
        # Create formatted output
        output = f"Instagram Image URLs for @{username}\n"
        output += "=" * 80 + "\n\n"
        output += f"Total Images Found: {len(all_urls)}\n"
        output += f"Total Posts: {urls_data.get('total_posts', 0)}\n"
        output += "=" * 80 + "\n\n"
        
        # Add URLs by post if available
        if urls_data.get('by_post'):
            for i, post in enumerate(urls_data['by_post'], 1):
                output += f"Post {i}: {post.get('post_id', 'Unknown')}\n"
                for j, url in enumerate(post.get('images', []), 1):
                    output += f"  Image {j}: {url}\n"
                output += "\n"
        else:
            # Just list all URLs
            for i, url in enumerate(all_urls, 1):
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

@app.route('/urls-json/<username>', methods=['GET'])
def urls_json(username):
    """Get URLs in clean JSON format"""
    username = username.replace('@', '').strip()
    result = run_spydox_extractor(username)
    
    if result.get('success'):
        return jsonify({
            "success": True,
            "username": username,
            "data": {
                "urls": result.get('image_urls', {}).get('all_urls', []),
                "posts": result.get('image_urls', {}).get('by_post', [])
            },
            "stats": {
                "total_images": result.get('total_images', 0),
                "total_posts": result.get('image_urls', {}).get('total_posts', 0)
            }
        })
    else:
        return jsonify(result)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
