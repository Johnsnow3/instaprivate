#!/usr/bin/env python3
# =========================================
#  Instagram Image Extractor
#  Works on Vercel
# =========================================

import os
import sys
import json
import time
import re
from urllib.parse import unquote

# Try to import requests, with helpful error
try:
    import requests
except ImportError:
    print("[!] Error: requests module not found")
    print("[!] Make sure it's in requirements.txt")
    sys.exit(1)

# Try to import BeautifulSoup
try:
    from bs4 import BeautifulSoup
except ImportError:
    print("[!] Error: beautifulsoup4 module not found")
    print("[!] Make sure it's in requirements.txt")
    sys.exit(1)

def banner():
    """Display banner"""
    print("\033[1;32m")  # Green color
    print("""
    ╔══╗╔╗─╔╗╔══╗╔══╗╔══╗╔╗─╔╗╔══╗╔══╗╔══╗╔╗╔╗
    ║╔╗║║║─║║╚╗╔╝║╔╗║║╔╗║║║─║║║╔╗║╚╗╔╝║╔═╝║╚╝║
    ║╚╝║║╚═╝║─║║─║║║║║╚╝║║╚═╝║║╚╝║─║║─║╚═╗║╔╗║
    ║╔╗║╚═╗╔╝─║║─║║║║║╔╗║╚═╗╔╝║╔╗║─║║─╚═╗║║║║║
    ║║║║╔╗║║─╔╝╚╗║╚╝║║║║║╔╗║║─║║║║╔╝╚╗╔═╝║║║╚╝║
    ╚╝╚╝╚╝╚╝─╚══╝╚══╝╚╝╚╝╚╝╚╝─╚╝╚╝╚══╝╚══╝╚╩══╝
    [+] Created By : SPYDOX
    [+] Tool Name  : INSTAGRAM IMAGE EXTRACTOR
    [+] Version    : VERGEL EDITION 2026
    """)
    print("\033[0m")  # Reset color

def fetch_instagram_profile(username):
    """Fetch Instagram profile page"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.instagram.com/',
    }
    
    url = f'https://www.instagram.com/{username}/'
    print(f"[*] Fetching profile: {username}")
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            print("[+] Successfully fetched profile page")
            return response
        else:
            print(f"[-] Error: Received status code {response.status_code}")
            return None
    except requests.exceptions.Timeout:
        print("[-] Error: Request timeout")
        return None
    except requests.exceptions.ConnectionError:
        print("[-] Error: Connection error")
        return None
    except Exception as e:
        print(f"[-] Error: {e}")
        return None

def extract_json_data(html_content):
    """Extract JSON data from script tags"""
    soup = BeautifulSoup(html_content, 'html.parser')
    script_tags = soup.find_all('script', {'type': 'application/json'})
    
    print(f"[*] Found {len(script_tags)} JSON script tags")
    
    for script in script_tags:
        content = script.string
        if not content or len(content) < 100:
            continue
        
        try:
            # Try to parse JSON
            data = json.loads(content)
            
            # Check if it contains profile data
            if any(key in content for key in ['edge_followed_by', 'edge_owner_to_timeline_media', 'profile_pic_url']):
                print("[+] Found script with profile data")
                return data
        except:
            continue
    
    print("[-] No profile data found in script tags")
    return None

def extract_image_urls(data):
    """Extract image URLs from JSON data"""
    image_urls = []
    
    def recursive_search(obj):
        if isinstance(obj, dict):
            # Look for display_url
            if 'display_url' in obj and isinstance(obj['display_url'], str):
                if obj['display_url'].startswith('http'):
                    image_urls.append(obj['display_url'])
            
            # Look for display_src
            if 'display_src' in obj and isinstance(obj['display_src'], str):
                if obj['display_src'].startswith('http'):
                    image_urls.append(obj['display_src'])
            
            # Look for image_versions2 (carousel posts)
            if 'image_versions2' in obj:
                candidates = obj['image_versions2'].get('candidates', [])
                for candidate in candidates:
                    if 'url' in candidate:
                        url = candidate['url']
                        if url.startswith('http'):
                            image_urls.append(url)
            
            # Look for carousel media
            if 'carousel_media' in obj and isinstance(obj['carousel_media'], list):
                for media in obj['carousel_media']:
                    recursive_search(media)
            
            # Recursively search values
            for value in obj.values():
                recursive_search(value)
        
        elif isinstance(obj, list):
            for item in obj:
                recursive_search(item)
    
    recursive_search(data)
    
    # Remove duplicates and clean URLs
    unique_urls = []
    for url in image_urls:
        # Decode URL if needed
        try:
            url = unquote(url)
        except:
            pass
        
        # Clean up URL
        url = url.split('?')[0]  # Remove query parameters for deduplication
        if url not in unique_urls and url.startswith('http'):
            unique_urls.append(url)
    
    return unique_urls

def save_urls_to_file(urls, filename='extracted_urls.txt'):
    """Save URLs to file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("Instagram Image URLs - Extracted via SPYDOX\n")
            f.write("=" * 60 + "\n")
            f.write(f"Total Images: {len(urls)}\n")
            f.write("=" * 60 + "\n\n")
            
            for i, url in enumerate(urls, 1):
                f.write(f"{i}. {url}\n")
        
        print(f"[+] Saved {len(urls)} image URLs to {filename}")
        return True
    except Exception as e:
        print(f"[-] Error saving file: {e}")
        return False

def main():
    """Main function"""
    banner()
    print("=" * 60)
    print("Instagram Image Extractor")
    print("=" * 60)
    print()
    
    # Get username from input
    try:
        username = sys.stdin.readline().strip()
        if not username:
            username = input("Enter Instagram username: ").strip()
    except:
        username = input("Enter Instagram username: ").strip()
    
    if not username:
        print("[-] Error: Username cannot be empty")
        return
    
    print(f"[*] Processing username: {username}")
    
    # Fetch profile
    response = fetch_instagram_profile(username)
    if not response:
        print("[-] Failed to fetch profile")
        return
    
    # Extract JSON data
    data = extract_json_data(response.text)
    if not data:
        print("[-] Failed to extract data")
        return
    
    # Extract image URLs
    urls = extract_image_urls(data)
    
    if urls:
        print(f"[+] Found {len(urls)} image URLs")
        
        # Save to file
        save_urls_to_file(urls)
        
        # Print first 5 URLs as sample
        print("\n[*] Sample URLs (first 5):")
        for i, url in enumerate(urls[:5], 1):
            print(f"  {i}. {url}")
        
        print(f"\n[+] Extraction complete! File saved as: extracted_urls.txt")
    else:
        print("[-] No image URLs found")

if __name__ == "__main__":
    main()
