from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, quote
import re

def chrome_view(request):
    if request.method == 'POST':
        url = request.POST.get('url')
        
        # Handle search queries
        if not any(url.startswith(prefix) for prefix in ['http://', 'https://', 'www.']):
            if ' ' in url or '.' not in url:
                search_query = quote(url)
                url = f'https://www.bing.com/search?q={search_query}'
            else:
                url = f'https://www.{url}'
        elif url.startswith('www.'):
            url = f'https://{url}'
        
        try:
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
            content_type = response.headers.get('content-type', '').lower()
            
            if 'text/html' in content_type:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Remove problematic headers
                for meta in soup.find_all('meta', {'http-equiv': ['Content-Security-Policy', 'X-Frame-Options']}):
                    meta.decompose()
                
                # Fix relative URLs and add target attributes
                base_url = response.url
                for tag in soup.find_all(['a', 'img', 'link', 'script', 'form']):
                    # Fix URLs
                    for attr in ['href', 'src', 'action']:
                        if tag.get(attr):
                            tag[attr] = urljoin(base_url, tag[attr])
                    
                    # Make links work within the iframe
                    if tag.name == 'a':
                        tag['target'] = '_self'
                        if tag.get('onclick'):
                            del tag['onclick']
                
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
                
                # Add script to handle link clicks
                script = soup.new_tag('script')
                script.string = """
                    document.addEventListener('click', function(e) {
                        if (e.target.tagName === 'A') {
                            e.preventDefault();
                            window.parent.postMessage({
                                type: 'navigation',
                                url: e.target.href
                            }, '*');
                        }
                    });
                """
                soup.body.append(script)
                
                return JsonResponse({
                    'status': 'success',
                    'content': str(soup),
                    'title': soup.title.string if soup.title else url,
                    'favicon': find_favicon(soup, base_url),
                    'url': response.url
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Cannot display this type of content ({content_type})'
                })
                
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
            
    return render(request, 'chrome.html')

def find_favicon(soup, base_url):
    favicon = None
    
    # Check link tags first
    for link in soup.find_all('link'):
        if any(rel in (link.get('rel', []) or []) for rel in ['icon', 'shortcut icon']):
            favicon = link.get('href')
            break
    
    # If no favicon found in links, try the default location
    if not favicon:
        parsed_url = urlparse(base_url)
        favicon = f"{parsed_url.scheme}://{parsed_url.netloc}/favicon.ico"
    
    return urljoin(base_url, favicon)
