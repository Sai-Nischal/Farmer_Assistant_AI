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
        # Vercel provides the original path in several places.
        # The most reliable for Flask is often the REQUEST_URI or X-Forwarded-Uri.
        path = environ.get('REQUEST_URI') or environ.get('HTTP_X_FORWARDED_URI') or environ.get('PATH_INFO')

        if path:
            # 1. Strip query strings
            path = path.split('?')[0]

            # 2. If it's a full URL, extract the path
            if '://' in path:
                from urllib.parse import urlparse
                path = urlparse(path).path

            # 3. Vercel often prefixes the path with /api/index when rewriting.
            # We must remove this so Flask sees the route defined in app.py (e.g., /diagnose)
            if path.startswith('/api/index'):
                path = path[len('/api/index'):]

            # 4. Ensure it starts with / and isn't empty
            if not path or path == '':
                path = '/'
            elif not path.startswith('/'):
                path = '/' + path

            environ['PATH_INFO'] = path

        # Final check: if Flask still sees /api/index, force it to root
        if environ.get('PATH_INFO') == '/api/index':
            environ['PATH_INFO'] = '/'

        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelWSGIMiddleware(app.wsgi_app)
