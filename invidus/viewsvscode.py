from django.shortcuts import render
from django.http import JsonResponse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def vscode_view(request):
    if request.method == 'POST':
        try:
            url = 'https://vscode.dev'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Cache-Control': 'max-age=0',
                'Upgrade-Insecure-Requests': '1'
            }
            
            session = requests.Session()
            response = session.get(url, headers=headers, timeout=10, allow_redirects=True)
            response.encoding = response.apparent_encoding
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove problematic headers
            for meta in soup.find_all('meta', {'http-equiv': ['Content-Security-Policy', 'X-Frame-Options']}):
                meta.decompose()
            
            # Fix relative URLs
            base_url = response.url
            for tag in soup.find_all(['link', 'script', 'img']):
                for attr in ['href', 'src']:
                    if tag.get(attr):
                        tag[attr] = urljoin(base_url, tag[attr])
            
            # Add base tag
            base_tag = soup.new_tag('base', href=base_url)
            if soup.head:
                soup.head.insert(0, base_tag)
            else:
                soup.insert(0, base_tag)
            
            # Add our own CSP meta tag
            csp_meta = soup.new_tag('meta')
            csp_meta['http-equiv'] = 'Content-Security-Policy'
            csp_meta['content'] = "default-src * 'unsafe-inline' 'unsafe-eval' data: blob:; frame-ancestors *;"
            soup.head.insert(0, csp_meta)
            
            return JsonResponse({
                'status': 'success',
                'content': str(soup),
                'title': 'Visual Studio Code',
                'favicon': '/static/images/vscode.png',
                'url': response.url
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
    
    return render(request, 'vscode.html')
