document.addEventListener('DOMContentLoaded', () => {
    // 1. Register PWA Service Worker
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
            navigator.serviceWorker.register('/static/service-worker.js')
                .then(registration => {
                    console.log('Rythu Mitra SW successfully registered:', registration.scope);
                })
                .catch(error => {
                    console.error('Rythu Mitra SW registration failed:', error);
                });
        });
    }

    // 2. Manage Network Status (Online / Offline banner)
    const updateOnlineStatus = () => {
        if (navigator.onLine) {
            document.body.classList.remove('offline-mode');
            console.log("App is online");
        } else {
            document.body.classList.add('offline-mode');
            console.log("App is offline - showing local cached shell");
        }
    };

    window.addEventListener('online', updateOnlineStatus);
    window.addEventListener('offline', updateOnlineStatus);
    
    // Check status immediately on boot
    updateOnlineStatus();

    // 3. Highlight current page in bottom navigation bar
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.bottom-nav a');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (currentPath === href || (href !== '/' && currentPath.startsWith(href))) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
});
