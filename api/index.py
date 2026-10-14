import os
import sys

# Add project root directory to sys.path so app, agents, services, and models are importable
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app

class VercelWSGIMiddleware:
    """
    WSGI middleware to fix Vercel serverless rewrite PATH_INFO behavior.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        # DIAGNOSTIC: Add a custom header to verify middleware runs
        original_path = environ.get('PATH_INFO', 'UNKNOWN')

        # Try to get the original path from Vercel headers
        path = (environ.get('HTTP_X_VERCEL_ORIGINAL_URL') or
                environ.get('HTTP_X_VERCEL_PATH') or
                environ.get('REQUEST_URI') or
                environ.get('HTTP_X_FORWARDED_URI') or
                environ.get('ORIGINAL_URI') or
                environ.get('HTTP_X_ORIGINAL_URL') or
                environ.get('HTTP_X_REWRITE_URL') or
                environ.get('PATH_INFO'))

        print(f"[MIDDLEWARE] Original PATH_INFO: {original_path}", file=sys.stderr)
        print(f"[MIDDLEWARE] X-Vercel-Original-URL: {environ.get('HTTP_X_VERCEL_ORIGINAL_URL')}", file=sys.stderr)
        print(f"[MIDDLEWARE] X-Vercel-Path: {environ.get('HTTP_X_VERCEL_PATH')}", file=sys.stderr)
        print(f"[MIDDLEWARE] REQUEST_URI: {environ.get('REQUEST_URI')}", file=sys.stderr)
        print(f"[MIDDLEWARE] X-Forwarded-Uri: {environ.get('HTTP_X_FORWARDED_URI')}", file=sys.stderr)

        if path:
            # 1. Strip query strings
            path = path.split('?')[0]

            # 2. If it's a full URL, extract the path
            if '://' in path:
                from urllib.parse import urlparse
                path = urlparse(path).path

            # 3. Vercel often prefixes the path with /api/index when rewriting.
            if path.startswith('/api/index'):
                path = path[len('/api/index'):]

            # 4. Ensure it starts with / and isn't empty
            if not path or path == '':
                path = '/'
            elif not path.startswith('/'):
                path = '/' + path

            environ['PATH_INFO'] = path
            print(f"[MIDDLEWARE] Final PATH_INFO: {path}", file=sys.stderr)

        # Final check: if Flask still sees /api/index, force it to root
        if environ.get('PATH_INFO') == '/api/index':
            environ['PATH_INFO'] = '/'

        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelWSGIMiddleware(app.wsgi_app)

# Simple test endpoint to verify routing works
from flask import jsonify, request

@app.route('/api/test-path')
def test_path():
    return jsonify({
        "path_info": request.environ.get('PATH_INFO'),
        "request_uri": request.environ.get('REQUEST_URI'),
        "vercel_original": request.environ.get('HTTP_X_VERCEL_ORIGINAL_URL'),
        "vercel_path": request.environ.get('HTTP_X_VERCEL_PATH'),
    })
