# =========================================
#  Instagram Private Post Extractor API
#  Working Version for Railway
# =========================================

import os
import requests
import json
import time
import re
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def extract_instagram_posts(username):
    """Extract Instagram post URLs for a given username"""
    try:
        print(f"[*] Fetching profile: {username}")
        
        # Clean username
        username = username.replace('@', '').strip().lower()
        
        # Updated headers to avoid blocking
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
        
        url = f'https://www.instagram.com/{username}/'
        
        # Add delay to avoid rate limiting
        time.sleep(1)
        
        # Make request
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 404:
            return {"success": False, "error": f"User '{username}' not found"}
        elif response.status_code == 429:
            return {"success": False, "error": "Rate limited. Please try again later"}
        elif response.status_code != 200:
            return {"success": False, "error": f"HTTP {response.status_code}"}
        
        print("[+] Successfully fetched page")
        
        # Look for JSON data in the HTML
        html_content = response.text
        
        # Method 1: Find shared data
        shared_data_pattern = r'window\._sharedData\s*=\s*({.*?});</script>'
        shared_match = re.search(shared_data_pattern, html_content)
        
        image_urls = []
        
        if shared_match:
            try:
                shared_data = json.loads(shared_match.group(1))
                
                # Navigate to media data
                entry_data = shared_data.get('entry_data', {})
                profile_pages = entry_data.get('ProfilePage', [])
                
                if profile_pages and len(profile_pages) > 0:
                    user_data = profile_pages[0].get('graphql', {}).get('user', {})
                    media_data = user_data.get('edge_owner_to_timeline_media', {})
                    edges = media_data.get('edges', [])
                    
                    for edge in edges:
                        node = edge.get('node', {})
                        post_id = node.get('id', 'unknown')
                        
                        # Get display URL
                        display_url = node.get('display_url', '')
                        if display_url:
                            image_urls.append({
                                'post_id': post_id,
                                'url': display_url,
                                'type': 'display'
                            })
                        
                        # Get thumbnail
                        thumbnail = node.get('thumbnail_src', '')
                        if thumbnail and thumbnail != display_url:
                            image_urls.append({
                                'post_id': post_id,
                                'url': thumbnail,
                                'type': 'thumbnail'
                            })
                        
                        # Check for multiple images in carousel
                        if node.get('edge_sidecar_to_children'):
                            children = node['edge_sidecar_to_children'].get('edges', [])
                            for child in children:
                                child_node = child.get('node', {})
                                child_url = child_node.get('display_url', '')
                                if child_url and child_url != display_url:
                                    image_urls.append({
                                        'post_id': post_id,
                                        'url': child_url,
                                        'type': 'carousel'
                                    })
            except Exception as e:
                print(f"[-] Error parsing shared data: {e}")
        
        # Method 2: Look for additional data in script tags
        if not image_urls:
            script_pattern = r'<script type="text/javascript">([^<]+)</script>'
            scripts = re.findall(script_pattern, html_content)
            
            for script in scripts:
                if 'display_url' in script:
                    # Extract URLs using regex
                    url_pattern = r'display_url":"(https:[^"]+)"'
                    urls = re.findall(url_pattern, script)
                    for url in urls[:20]:  # Limit to 20
                        image_urls.append({
                            'post_id': 'unknown',
                            'url': url.replace('\\u0026', '&'),
                            'type': 'extracted'
                        })
        
        # Remove duplicates
        unique_urls = []
        seen = set()
        for item in image_urls:
            if item['url'] not in seen:
                seen.add(item['url'])
                unique_urls.append(item)
        
        if not unique_urls:
            return {"success": False, "error": "No image URLs found. Profile might be private or have no posts."}
        
        posts_count = len(set([item['post_id'] for item in unique_urls if item['post_id'] != 'unknown']))
        
        print(f"[+] Found {len(unique_urls)} image URLs")
        
        # Generate file content
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        file_content = f"""Instagram Private Post URLs - Extraction Results
================================================================================

Username: {username}
Total Posts: {posts_count if posts_count > 0 else 'Unknown'}
Total Images: {len(unique_urls)}
Extraction Time: {timestamp}

================================================================================

"""
        
        for i, item in enumerate(unique_urls, 1):
            file_content += f"[{i}] Post ID: {item['post_id']}\n"
            file_content += f"    Type: {item['type']}\n"
            file_content += f"    URL: {item['url']}\n"
            file_content += "-" * 60 + "\n"
        
        file_content += f"\n[+] Total URLs extracted: {len(unique_urls)}"
        
        return {
            "success": True,
            "username": username,
            "posts_count": posts_count,
            "images_count": len(unique_urls),
            "image_urls": unique_urls,
            "file_content": file_content,
            "timestamp": timestamp
        }
        
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Request timeout"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Connection error"}
    except Exception as e:
        print(f"[-] Error: {str(e)}")
        return {"success": False, "error": str(e)}

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "service": "Instagram Extractor API",
        "version": "1.0",
        "endpoints": {
            "/extract/<username>": "GET - Extract Instagram posts",
            "/extract": "POST - Send JSON with username"
        }
    })

@app.route('/extract/<username>', methods=['GET'])
def extract_get(username):
    result = extract_instagram_posts(username)
    return jsonify(result)

@app.route('/extract', methods=['POST'])
def extract_post():
    data = request.get_json()
    if not data or 'username' not in data:
        return jsonify({"success": False, "error": "Username required"}), 400
    
    username = data['username'].replace('@', '').strip()
    result = extract_instagram_posts(username)
    return jsonify(result)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "time": time.time()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"[+] Starting Instagram Extractor API on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
