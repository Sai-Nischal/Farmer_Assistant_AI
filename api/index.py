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
        # Recover original path from Vercel headers
        path = environ.get('HTTP_X_FORWARDED_URI') or environ.get('REQUEST_URI')

        if path:
            # If full URL, extract path only
            if '://' in path:
                parts = path.split('/', 3)
                path = parts[3] if len(parts) > 3 else '/'
                if not path.startswith('/'):
                    path = '/' + path

            # Remove the destination prefix so Flask sees the actual route
            path = path.replace('/api/index', '', 1)

            if not path or path == '':
                path = '/'

            environ['PATH_INFO'] = path

        # Final safety: if it's still the function path, route to root
        if environ.get('PATH_INFO') == '/api/index':
            environ['PATH_INFO'] = '/'

        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelWSGIMiddleware(app.wsgi_app)
