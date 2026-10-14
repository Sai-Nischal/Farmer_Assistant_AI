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
    Runs BEFORE Flask routing, so it can fix the path in time.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        # Get the original path from Vercel headers
        # Vercel sets x-vercel-original-url header with the full original URL
        original_url = environ.get('HTTP_X_VERCEL_ORIGINAL_URL')

        if original_url:
            from urllib.parse import urlparse
            parsed = urlparse(original_url)
            path = parsed.path

            # Remove query string
            if '?' in path:
                path = path.split('?')[0]

            if path and path != '/':
                environ['PATH_INFO'] = path
        else:
            # Fallback: check x-vercel-path header
            vercel_path = environ.get('HTTP_X_VERCEL_PATH')
            if vercel_path:
                environ['PATH_INFO'] = vercel_path
            else:
                # Final fallback: fix /api/index prefix
                path_info = environ.get('PATH_INFO', '')
                if path_info == '/api/index':
                    environ['PATH_INFO'] = '/'
                elif path_info.startswith('/api/index/'):
                    environ['PATH_INFO'] = path_info[len('/api/index'):]

        return self.wsgi_app(environ, start_response)

# Apply the middleware BEFORE any routes are processed
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
