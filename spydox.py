import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import unquote
import time
import sys
import random

def banner():
    # Simple banner without any identifiers
    print("\033[1;36m")  # Cyan color
    print("""
╔══════════════════════════════════════════════════════════╗
║         Instagram Media Extractor - Research Tool        ║
║                 For Educational Purposes Only            ║
╚══════════════════════════════════════════════════════════╝
    """)
    print("\033[0m") # Color reset

# Rotating user agents to avoid detection
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPad; CPU OS 17_1_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0',
]

# Multiple header configurations to rotate through
HEADER_TEMPLATES = [
    {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'accept-language': 'en-US,en;q=0.5',
        'accept-encoding': 'gzip, deflate, br',
        'dnt': '1',
        'connection': 'keep-alive',
        'upgrade-insecure-requests': '1',
    },
    {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'accept-language': 'en-GB,en;q=0.9',
        'accept-encoding': 'gzip, deflate, br',
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
    },
    {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'accept-language': 'en-US,en;q=0.9',
        'accept-encoding': 'gzip, deflate',
        'connection': 'keep-alive',
        'upgrade-insecure-requests': '1',
    }
]

def get_random_headers():
    """Generate random headers to avoid fingerprinting"""
    headers = random.choice(HEADER_TEMPLATES).copy()
    headers['user-agent'] = random.choice(USER_AGENTS)
    
    # Add random but realistic headers
    if random.choice([True, False]):
        headers['viewport-width'] = str(random.choice([1920, 1536, 1366, 1280, 375, 390]))
    
    return headers

def fetch_instagram_profile(username):
    """
    Fetches Instagram profile page for the given username with rotating headers.
    """
    url = f'https://www.instagram.com/{username}/'
    
    # Try with different headers if first attempt fails
    max_attempts = 3
    for attempt in range(max_attempts):
        headers = get_random_headers()
        print(f"[*] Fetching profile: {username} (Attempt {attempt + 1}/{max_attempts})")
        
        try:
            # Add small delay between attempts
            if attempt > 0:
                time.sleep(random.uniform(2, 4))
            
            response = requests.get(
                url, 
                headers=headers, 
                timeout=15,
                allow_redirects=True
            )
            
            if response.status_code == 200:
                print("[+] Successfully fetched profile page")
                return response
            elif response.status_code == 429:
                print(f"[-] Rate limited (429). Waiting longer before retry...")
                time.sleep(random.uniform(5, 10))
            elif response.status_code == 403:
                print(f"[-] Access forbidden (403). Trying different headers...")
            else:
                print(f"[-] Received status code {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"[-] Request timeout on attempt {attempt + 1}")
        except requests.exceptions.ConnectionError:
            print(f"[-] Connection error on attempt {attempt + 1}")
        except requests.exceptions.RequestException as e:
            print(f"[-] Request error: {e}")
    
    print("[-] Failed to fetch profile after multiple attempts")
    return None

def extract_timeline_data(html_content):
    """Extract timeline data from Instagram page"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Try multiple script tag patterns
        script_patterns = [
            {'type': 'application/json'},
            {'type': 'text/javascript'},
            {'id': '__NEXT_DATA__'},
            {'id': 'additionalData'}
        ]
        
        all_scripts = []
        for pattern in script_patterns:
            scripts = soup.find_all('script', pattern)
            all_scripts.extend(scripts)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_scripts = []
        for script in all_scripts:
            if script.string and script.string not in seen:
                seen.add(script.string)
                unique_scripts.append(script)
        
        print(f"[*] Found {len(unique_scripts)} unique script tags")

        for script in unique_scripts:
            if script.string:
                script_content = script.string
                
                # Look for Instagram data patterns
                instagram_patterns = [
                    'edge_owner_to_timeline_media',
                    'graphql',
                    'user',
                    'media',
                    'image_versions2',
                    'display_url',
                    'display_src'
                ]
                
                # Check if content contains Instagram data
                content_lower = script_content.lower()
                if any(pattern in content_lower for pattern in instagram_patterns):
                    try:
                        # Try to parse JSON
                        data = json.loads(script_content)
                        
                        # Verify it contains media data
                        if 'graphql' in str(data) or 'media' in str(data):
                            print("[+] Found script with media data")
                            return data
                    except json.JSONDecodeError:
                        # Try to extract JSON from within JavaScript
                        try:
                            import re
                            # Look for JSON object in JavaScript
                            json_match = re.search(r'({.*})', script_content, re.DOTALL)
                            if json_match:
                                data = json.loads(json_match.group(1))
                                print("[+] Extracted JSON data from script")
                                return data
                        except:
                            continue

        print("[-] Media data not found in any script tag")
        return None
        
    except Exception as e:
        print(f"[-] Error extracting data: {e}")
        return None

def decode_url(escaped_url):
    """Decode URL with multiple methods"""
    try:
        # Try unicode escape first
        decoded = escaped_url.encode('utf-8').decode('unicode_escape')
    except:
        decoded = escaped_url

    # URL decode
    decoded = unquote(decoded)
    
    # Handle Instagram CDN URLs
    if 'cdninstagram.com' in decoded and '\\u0026' in decoded:
        decoded = decoded.replace('\\u0026', '&')
    
    return decoded

def extract_all_image_urls_recursive(obj, urls=None, post_id=None):
    """Recursively extract all image URLs from Instagram data"""
    if urls is None:
        urls = set()

    if isinstance(obj, dict):
        # Capture post ID
        if 'id' in obj and isinstance(obj.get('id'), (str, int)) and 'post' in str(obj):
            post_id = str(obj['id'])
        elif 'pk' in obj and isinstance(obj.get('pk'), (str, int)):
            post_id = str(obj['pk'])
        elif 'code' in obj and isinstance(obj.get('code'), str):
            post_id = obj['code']

        # Look for image URLs in various Instagram structures
        image_patterns = [
            ('image_versions2', 'candidates'),
            ('display_resources', None),
            ('display_src', None),
            ('display_url', None),
            ('thumbnail_src', None),
        ]
        
        for pattern, subpattern in image_patterns:
            if pattern in obj:
                if subpattern and isinstance(obj[pattern], dict) and subpattern in obj[pattern]:
                    candidates = obj[pattern][subpattern]
                    if isinstance(candidates, list):
                        for candidate in candidates:
                            if isinstance(candidate, dict):
                                url = candidate.get('src') or candidate.get('url')
                                if url:
                                    height = candidate.get('height', 0)
                                    width = candidate.get('width', 0)
                                    resolution = f"{width}x{height}" if width and height else "unknown"
                                    decoded_url = decode_url(url)
                                    urls.add((post_id or 'unknown', resolution, decoded_url))
                
                elif isinstance(obj[pattern], str):
                    url = obj[pattern]
                    decoded_url = decode_url(url)
                    urls.add((post_id or 'unknown', 'unknown', decoded_url))

        # Recursively process all values
        for value in obj.values():
            extract_all_image_urls_recursive(value, urls, post_id)

    elif isinstance(obj, list):
        for item in obj:
            extract_all_image_urls_recursive(item, urls, post_id)

    return urls

def save_urls_to_file(image_urls, filename='instagram_media_urls.txt'):
    """Save extracted URLs to file"""
    urls_by_post = {}
    for post_id, resolution, url in image_urls:
        if post_id not in urls_by_post:
            urls_by_post[post_id] = []
        urls_by_post[post_id].append((resolution, url))

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("Instagram Media URLs - Research Data\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Extraction Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Posts Found: {len(urls_by_post)}\n")
            f.write(f"Total Media URLs: {len(image_urls)}\n\n")
            f.write("=" * 80 + "\n\n")

            # Sort posts by ID for consistency
            sorted_posts = sorted(urls_by_post.items())
            
            for post_id, resolutions in sorted_posts:
                f.write(f"POST ID: {post_id}\n")
                f.write(f"Media Items: {len(resolutions)}\n")
                f.write("-" * 80 + "\n")

                for i, (resolution, url) in enumerate(resolutions, 1):
                    f.write(f"\n  Media {i}:\n")
                    f.write(f"  Resolution: {resolution}\n")
                    f.write(f"  URL: {url}\n")

                f.write("\n" + "=" * 80 + "\n\n")

        print(f"[+] Saved {len(image_urls)} URLs from {len(urls_by_post)} posts to {filename}")
        return True
    except Exception as e:
        print(f"[-] Error saving to file: {e}")
        return False

def display_results_summary(image_urls):
    """Display summary of extracted data"""
    urls_list = sorted(list(image_urls), key=lambda x: (x[0], x[1]))
    posts_count = len(set(url[0] for url in urls_list))
    
    # Count resolutions
    resolutions = {}
    for _, resolution, _ in urls_list:
        resolutions[resolution] = resolutions.get(resolution, 0) + 1

    print()
    print("=" * 80)
    print("EXTRACTION SUMMARY")
    print("=" * 80)
    print(f"Total Posts Found: {posts_count}")
    print(f"Total Media URLs: {len(urls_list)}")
    print("\nResolution Distribution:")
    for res, count in sorted(resolutions.items(), key=lambda x: int(x[0].split('x')[0]) if 'x' in x[0] else 0, reverse=True)[:5]:
        print(f"  {res}: {count} images")
    print("=" * 80)
    print()

def main(username=None):
    """Main function"""
    # Display banner
    banner()

    print("=" * 80)
    print("Instagram Media Extractor - Research Tool")
    print("For Educational and Research Purposes Only")
    print("=" * 80)
    print()

    # Get username from parameter or prompt
    if not username:
        try:
            username = input("Enter Instagram username to analyze: ").strip()
        except EOFError:
            print("[-] Cannot read input. Please provide username as argument.")
            print("Usage: python script.py <username>")
            return

    if not username:
        print("[-] Error: Username cannot be empty")
        return

    print()
    print("[!] DISCLAIMER: This tool is for educational purposes only.")
    print("[!] Only use on accounts you own or have permission to analyze.")
    print("[!] Respect Instagram's Terms of Service and rate limits.")
    print()

    time.sleep(2)

    # Fetch profile
    response = fetch_instagram_profile(username)

    if not response:
        print("[-] Failed to fetch profile page")
        return

    # Extract data
    timeline_data = extract_timeline_data(response.text)

    if not timeline_data:
        print("[-] Failed to extract media data")
        return

    print()
    print("[*] Extracting all media URLs recursively...")
    print("[*] This may take a moment depending on the number of posts...")
    
    image_urls = extract_all_image_urls_recursive(timeline_data)

    if not image_urls:
        print("[-] No media URLs found")
        return

    # Display results
    display_results_summary(image_urls)

    # Save to file
    filename = f"instagram_{username}_media_urls.txt"
    save_urls_to_file(image_urls, filename)

    print()
    print("[+] Analysis Complete")
    print(f"[*] Results saved to: {filename}")
    print()

if __name__ == "__main__":
    # Handle command line arguments
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()
