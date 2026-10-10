"""Authenticated retrieval service compatible with HC Instagram Auto-Sync 1.1.0."""
import re
import secrets
import threading
import time
from collections import OrderedDict
from fastapi import FastAPI, Header, HTTPException, Response
import instaloader
from collector import collect
from config import Settings


def make_loader(settings):
    loader = instaloader.Instaloader(max_connection_attempts=1, request_timeout=10, quiet=True)
    if settings.session_user:
        loader.load_session_from_file(settings.session_user, settings.session_file)
    return loader


def create_app(settings=None, loader=None, profile_factory=None, clock=time.time):
    settings = settings or Settings.from_environment()
    loader = loader or make_loader(settings)
    profile_factory = profile_factory or instaloader.Profile.from_username
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    lock = threading.Lock()
    cache = OrderedDict()

    def require_auth(value):
        if not secrets.compare_digest(value.encode('utf-8'), ('Bearer ' + settings.token).encode('utf-8')):
            raise HTTPException(401, 'Unauthorized')

    @app.middleware('http')
    async def security_headers(request, call_next):
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    @app.get('/health')
    def health():
        # Connectivity only, not a claim of Instagram collection capability.
        return {'ok': True}

    @app.get('/status')
    def status(authorization: str = Header(default='')):
        require_auth(authorization)
        return {'ok': True, 'service_version': '1.1.0',
                'stories_session_loaded': bool(loader.context.is_logged_in),
                'cached_queries': len(cache), 'busy': lock.locked()}

    @app.get('/feed/{username}')
    def feed(username: str, response: Response, types: str = 'media,stories', authorization: str = Header(default='')):
        require_auth(authorization)
        username = username.lower()
        if not re.fullmatch(r'[a-z0-9_.]{1,30}', username) or ('*' not in settings.allowed and username not in settings.allowed):
            raise HTTPException(404, 'Creator not registered')
        requested = set(types.split(','))
        if not requested or not requested <= {'media', 'stories'}:
            raise HTTPException(400, 'Invalid content types')
        if not lock.acquire(timeout=1):
            raise HTTPException(503, 'Worker busy; retry later', headers={'Retry-After': '300'})
        try:
            now = int(clock())
            key = (username, tuple(sorted(requested)))
            prior = cache.get(key)
            if prior and now - prior[0] < settings.cooldown:
                response.headers['X-HC-Cache'] = 'hit'
                return prior[1]
            try:
                data = collect(loader, profile_factory, username, requested, now)
            except ValueError:
                raise HTTPException(403, 'Public accounts only')
            except Exception:
                # Do not expose Instagram responses, session material or server paths.
                raise HTTPException(502, 'Instagram retrieval unavailable')
            cache[key] = (now, data)
            cache.move_to_end(key)
            while len(cache) > 4000:
                cache.popitem(last=False)
            response.headers['X-HC-Cache'] = 'miss'
            return data
        finally:
            lock.release()

    return app

# Uvicorn factory mode prevents environment loading during test imports.
