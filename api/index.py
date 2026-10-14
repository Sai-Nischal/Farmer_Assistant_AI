import os
import sys

# Add project root directory to sys.path so app, agents, services, and models are importable
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app
from flask import jsonify, request, redirect

# WSGI middleware to fix Vercel path
class VercelWSGIMiddleware:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        original_url = environ.get('HTTP_X_VERCEL_ORIGINAL_URL')
        if original_url:
            from urllib.parse import urlparse
            parsed = urlparse(original_url)
            path = parsed.path
            if '?' in path:
                path = path.split('?')[0]
            if path and path != '/':
                environ['PATH_INFO'] = path
        else:
            vercel_path = environ.get('HTTP_X_VERCEL_PATH')
            if vercel_path:
                environ['PATH_INFO'] = vercel_path
            else:
                path_info = environ.get('PATH_INFO', '')
                if path_info == '/api/index':
                    environ['PATH_INFO'] = '/'
                elif path_info.startswith('/api/index/'):
                    environ['PATH_INFO'] = path_info[len('/api/index'):]
        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelWSGIMiddleware(app.wsgi_app)

# Catch-all route that manually dispatches based on x-vercel-original-url
# This works even if middleware doesn't run in time for routing
@app.route('/api/index', defaults={'subpath': ''})
@app.route('/api/index/', defaults={'subpath': ''})
@app.route('/api/index/<path:subpath>')
def vercel_dispatch(subpath):
    """
    Handle Vercel's rewrite to /api/index by reading the original URL header
    and manually dispatching to the correct view function.
    """
    # Get original URL from Vercel header
    original_url = request.headers.get('x-vercel-original-url')

    if original_url:
        from urllib.parse import urlparse
        parsed = urlparse(original_url)
        path = parsed.path
        if '?' in path:
            path = path.split('?')[0]
    else:
        # Fallback: use subpath from the route
        path = '/' + subpath if subpath else '/'

    # DEBUG
    print(f"[DISPATCH] original_url: {original_url}", file=sys.stderr)
    print(f"[DISPATCH] path: {path}", file=sys.stderr)
    print(f"[DISPATCH] subpath: {subpath}", file=sys.stderr)
    print(f"[DISPATCH] route_map keys: {list(route_map.keys())}", file=sys.stderr)

    # Map paths to view functions
    route_map = {
        '/': 'home',
        '/diagnose': 'diagnose',
        '/advisory': 'advisory',
        '/schemes': 'schemes',
        '/history': 'history',
        '/settings': 'settings',
        '/dashboard': 'index',
        '/login': 'login',
        '/logout': 'logout',
        '/register': 'register',
        '/login/demo': 'login_demo',
        '/toggle-lang': 'toggle_lang',
        '/api/chat': 'api_chat',
        '/api/voice-output': 'api_voice_output',
        '/api/voice-input': 'api_voice_input',
    }

    # Handle dynamic routes
    if path.startswith('/static/'):
        # Let Flask handle static files normally
        pass
    elif path in route_map:
        view_func = app.view_functions.get(route_map[path])
        if view_func:
            print(f"[DISPATCH] Calling view: {route_map[path]}", file=sys.stderr)
            return view_func()
        else:
            print(f"[DISPATCH] View function not found for: {route_map[path]}", file=sys.stderr)

    # Default to home
    print(f"[DISPATCH] Defaulting to home", file=sys.stderr)
    return app.view_functions['home']()

# Test endpoint
@app.route('/api/test-path')
def test_path():
    return jsonify({
        "path_info": request.environ.get('PATH_INFO'),
        "request_uri": request.environ.get('REQUEST_URI'),
        "vercel_original": request.environ.get('HTTP_X_VERCEL_ORIGINAL_URL'),
        "vercel_path": request.environ.get('HTTP_X_VERCEL_PATH'),
    })

# Simple test route to verify route registration works
@app.route('/api/test-route')
def test_route():
    return jsonify({"status": "ok", "message": "Route registered successfully"})
