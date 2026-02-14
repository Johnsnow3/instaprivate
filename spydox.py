import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import unquote, urlparse, parse_qs
import time
import sys
import random
import re

def banner():
    print("\033[1;36m")
    print("""
╔══════════════════════════════════════════════════════════╗
║         Instagram Media Extractor - Research Tool        ║
║                 For Educational Purposes Only            ║
╚══════════════════════════════════════════════════════════╝
    """)
    print("\033[0m")

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
]

def get_random_headers():
    return {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'accept-language': 'en-US,en;q=0.5',
        'accept-encoding': 'gzip, deflate, br',
        'dnt': '1',
        'connection': 'keep-alive',
        'upgrade-insecure-requests': '1',
        'user-agent': random.choice(USER_AGENTS),
    }

def extract_json_from_html(html_content):
    """Extract JSON data from HTML using multiple methods"""
    json_data = {}
    
    # Method 1: Look for __sharedData__ (older Instagram)
    shared_data_match = re.search(r'window\._sharedData\s*=\s*({.*?});', html_content, re.DOTALL)
    if shared_data_match:
        try:
            json_data['shared_data'] = json.loads(shared_data_match.group(1))
            print("[+] Found _sharedData JSON")
        except:
            pass
    
    # Method 2: Look for __additionalData
    additional_data_match = re.search(r'window\.__additionalDataLoaded\s*\(\s*[\'"]([^\'"]+)[\'"]\s*,\s*({.*?})\s*\)\s*;', html_content, re.DOTALL)
    if additional_data_match:
        try:
            json_data['additional_data'] = json.loads(additional_data_match.group(2))
            print("[+] Found __additionalData JSON")
        except:
            pass
    
    # Method 3: Look for __instadate
    insta_date_match = re.search(r'window\.__instadate\s*=\s*({.*?});', html_content, re.DOTALL)
    if insta_date_match:
        try:
            json_data['insta_date'] = json.loads(insta_date_match.group(1))
            print("[+] Found __instadate JSON")
        except:
            pass
    
    # Method 4: Look for __APOLLO_STATE__
    apollo_match = re.search(r'window\.__APOLLO_STATE__\s*=\s*({.*?});', html_content, re.DOTALL)
    if apollo_match:
        try:
            json_data['apollo_state'] = json.loads(apollo_match.group(1))
            print("[+] Found __APOLLO_STATE__ JSON")
        except:
            pass
    
    # Method 5: Look for __ROOT_QUERY__
    root_query_match = re.search(r'window\.__ROOT_QUERY__\s*=\s*({.*?});', html_content, re.DOTALL)
    if root_query_match:
        try:
            json_data['root_query'] = json.loads(root_query_match.group(1))
            print("[+] Found __ROOT_QUERY__ JSON")
        except:
            pass
    
    # Method 6: Look for any large JSON object in script tags
    soup = BeautifulSoup(html_content, 'html.parser')
    for script in soup.find_all('script'):
        if script.string:
            # Look for JSON-like content
            json_match = re.search(r'({[\s\S]*})', script.string)
            if json_match:
                try:
                    potential_json = json_match.group(1)
                    # Try to parse it
                    parsed = json.loads(potential_json)
                    if isinstance(parsed, dict) and len(str(parsed)) > 1000:  # Only store large JSON objects
                        json_data[f'script_json_{len(json_data)}'] = parsed
                        print(f"[+] Found JSON in script tag ({len(str(parsed))} chars)")
                except:
                    pass
    
    return json_data

def extract_media_from_graphql(data):
    """Extract media URLs from GraphQL data structure"""
    urls = set()
    
    def recursive_extract(obj, path=""):
        if isinstance(obj, dict):
            # Look for common Instagram media patterns
            if 'display_url' in obj and obj['display_url']:
                urls.add(('unknown', 'unknown', obj['display_url']))
            
            if 'display_src' in obj and obj['display_src']:
                urls.add(('unknown', 'unknown', obj['display_src']))
            
            if 'thumbnail_src' in obj and obj['thumbnail_src']:
                urls.add(('unknown', 'unknown', obj['thumbnail_src']))
            
            # Check for image versions
            if 'image_versions2' in obj:
                candidates = obj['image_versions2'].get('candidates', [])
                for candidate in candidates:
                    if 'url' in candidate:
                        url = candidate['url']
                        height = candidate.get('height', 0)
                        width = candidate.get('width', 0)
                        resolution = f"{width}x{height}" if width and height else "unknown"
                        urls.add(('unknown', resolution, url))
            
            # Check for display_resources
            if 'display_resources' in obj:
                for resource in obj['display_resources']:
                    if 'src' in resource:
                        url = resource['src']
                        height = resource.get('config_height', 0)
                        width = resource.get('config_width', 0)
                        resolution = f"{width}x{height}" if width and height else "unknown"
                        urls.add(('unknown', resolution, url))
            
            # Recursively process all values
            for key, value in obj.items():
                if isinstance(value, (dict, list)):
                    recursive_extract(value, f"{path}.{key}" if path else key)
        
        elif isinstance(obj, list):
            for item in obj:
                recursive_extract(item, path)
    
    recursive_extract(data)
    return urls

def extract_media_from_apollo_state(data):
    """Extract media URLs from Apollo state data"""
    urls = set()
    
    for key, value in data.items():
        if isinstance(value, dict):
            # Look for media nodes
            if value.get('__typename') in ['GraphImage', 'GraphVideo', 'GraphSidecar']:
                if 'display_url' in value:
                    urls.add(('unknown', 'unknown', value['display_url']))
                
                # Check for dimensions
                if 'dimensions' in value:
                    dims = value['dimensions']
                    width = dims.get('width', 0)
                    height = dims.get('height', 0)
                    resolution = f"{width}x{height}" if width and height else "unknown"
                    
                    # Re-add with resolution
                    urls_list = list(urls)
                    urls.clear()
                    for pid, res, url in urls_list:
                        if url == value.get('display_url', ''):
                            urls.add((pid, resolution, url))
                        else:
                            urls.add((pid, res, url))
            
            # Check for thumbnail resources
            if 'thumbnail_resources' in value:
                for resource in value['thumbnail_resources']:
                    if 'src' in resource:
                        urls.add(('unknown', 'unknown', resource['src']))
    
    return urls

def fetch_instagram_profile_enhanced(username):
    """
    Enhanced Instagram profile fetcher with multiple methods
    """
    # Try direct profile page
    url = f'https://www.instagram.com/{username}/'
    
    # Also try API endpoints
    api_urls = [
        f'https://www.instagram.com/api/v1/users/web_profile_info/?username={username}',
        f'https://i.instagram.com/api/v1/users/web_profile_info/?username={username}',
        f'https://www.instagram.com/{username}/?__a=1&__d=dis',
    ]
    
    headers = get_random_headers()
    
    # Method 1: Try direct page
    print(f"[*] Attempting to fetch profile: {username}")
    try:
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            print("[+] Successfully fetched profile page")
            return response.text
    except Exception as e:
        print(f"[-] Direct fetch failed: {e}")
    
    # Method 2: Try API endpoints
    for i, api_url in enumerate(api_urls, 1):
        print(f"[*] Trying API endpoint {i}...")
        try:
            time.sleep(random.uniform(1, 3))
            api_headers = headers.copy()
            api_headers['x-requested-with'] = 'XMLHttpRequest'
            
            response = session.get(api_url, headers=api_headers, timeout=10)
            if response.status_code == 200:
                print(f"[+] API endpoint {i} successful")
                return response.text
        except:
            continue
    
    return None

def main(username=None):
    banner()
    
    print("=" * 80)
    print("Instagram Media Extractor - Research Tool")
    print("For Educational and Research Purposes Only")
    print("=" * 80)
    print()

    if not username:
        try:
            username = input("Enter Instagram username to analyze: ").strip()
        except EOFError:
            print("[-] Cannot read input. Please provide username as argument.")
            return

    if not username:
        print("[-] Error: Username cannot be empty")
        return

    print()
    print("[!] DISCLAIMER: This tool is for educational purposes only.")
    print("[!] Only use on accounts you own or have permission to analyze.")
    print()

    time.sleep(2)

    # Fetch profile with enhanced method
    html_content = fetch_instagram_profile_enhanced(username)

    if not html_content:
        print("[-] Failed to fetch profile page")
        return

    # Extract JSON data from HTML
    print("\n[*] Extracting JSON data from page...")
    json_data = extract_json_from_html(html_content)
    
    all_urls = set()
    
    # Process each JSON data source
    for data_source, data in json_data.items():
        print(f"\n[*] Processing {data_source}...")
        
        # Try to extract media from GraphQL structure
        urls = extract_media_from_graphql(data)
        if urls:
            print(f"[+] Found {len(urls)} media URLs in {data_source}")
            all_urls.update(urls)
        
        # Try Apollo state extraction
        if 'apollo_state' in data_source or isinstance(data, dict):
            apollo_urls = extract_media_from_apollo_state(data)
            if apollo_urls:
                print(f"[+] Found {len(apollo_urls)} media URLs in Apollo state")
                all_urls.update(apollo_urls)
    
    # Also try direct regex for image URLs
    print("\n[*] Scanning for direct image URLs...")
    image_pattern = r'https?://[^\s"\']+\.(?:jpg|jpeg|png|gif|webp)[^\s"\']*'
    direct_urls = re.findall(image_pattern, html_content)
    
    if direct_urls:
        # Filter Instagram CDN URLs
        insta_urls = [url for url in direct_urls if 'cdninstagram.com' in url or 'fbcdn.net' in url]
        for url in insta_urls[:50]:  # Limit to avoid duplicates
            all_urls.add(('unknown', 'unknown', url))
        print(f"[+] Found {len(insta_urls)} direct image URLs")
    
    if not all_urls:
        print("[-] No media URLs found")
        return
    
    # Display results
    print("\n" + "=" * 80)
    print(f"EXTRACTION SUMMARY")
    print("=" * 80)
    print(f"Total Media URLs Found: {len(all_urls)}")
    
    # Sample some URLs
    print("\nSample URLs (first 5):")
    for i, (_, _, url) in enumerate(list(all_urls)[:5]):
        print(f"  {i+1}. {url[:100]}...")
    
    print("=" * 80)
    print()
    
    # Save to file
    filename = f"instagram_{username}_media_urls.txt"
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"Instagram Media URLs for @{username}\n")
            f.write(f"Extracted: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            
            for i, (_, resolution, url) in enumerate(sorted(all_urls), 1):
                f.write(f"{i}. {url}\n")
                if resolution != 'unknown':
                    f.write(f"   Resolution: {resolution}\n")
        
        print(f"[+] Saved {len(all_urls)} URLs to {filename}")
    except Exception as e:
        print(f"[-] Error saving file: {e}")
    
    print()
    print("[+] Analysis Complete")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()
