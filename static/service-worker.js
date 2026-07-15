const CACHE_NAME = 'rythu-mitra-cache-v1';
const OFFLINE_URLS = [
    '/',
    '/diagnose',
    '/advisory',
    '/schemes',
    '/history',
    '/settings',
    '/static/css/style.css',
    '/static/js/main.js',
    '/static/js/diagnose.js',
    '/static/js/voice.js',
    '/static/manifest.json'
];

// Install Event
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => {
            console.log('PWA Service Worker caching app shell resources');
            return cache.addAll(OFFLINE_URLS);
        }).then(() => self.skipWaiting())
    );
});

// Activate Event
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(keys => {
            return Promise.all(
                keys.map(key => {
                    if (key !== CACHE_NAME) {
                        console.log('PWA SW clearing old cache:', key);
                        return caches.delete(key);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

// Fetch Event
self.addEventListener('fetch', event => {
    // Only handle GET requests
    if (event.request.method !== 'GET') return;

    // Check if the request is an HTML page or static asset
    const isNavigation = event.request.mode === 'navigate';
    
    if (isNavigation) {
        // Network-First strategy for pages so we always get live advisory/weather if online
        event.respondWith(
            fetch(event.request)
                .then(response => {
                    // Cache the fresh page
                    const copy = response.clone();
                    caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy));
                    return response;
                })
                .catch(() => {
                    // Fall back to cached shell page if offline
                    return caches.match(event.request).then(cachedResponse => {
                        return cachedResponse || caches.match('/');
                    });
                })
        );
    } else {
        // Cache-First, falling back to network strategy for static assets
        event.respondWith(
            caches.match(event.request).then(cachedResponse => {
                if (cachedResponse) {
                    return cachedResponse;
                }
                return fetch(event.request).then(response => {
                    // Cache new static resource
                    if (response.status === 200 && response.type === 'basic') {
                        const copy = response.clone();
                        caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy));
                    }
                    return response;
                }).catch(() => {
                    // Safe fallback if offline
                    return new Response('', { status: 404, statusText: 'Offline asset not found' });
                });
            })
        );
    }
});
