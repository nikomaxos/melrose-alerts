self.addEventListener('push', function(event) {
    let payload = { title: 'Melrose Alert', body: 'New alert received' };
    
    if (event.data) {
        try {
            payload = event.data.json();
        } catch (e) {
            payload.body = event.data.text();
        }
    }
    
    const options = {
        body: payload.body,
        icon: '/vite.svg', // Fallback icon
        badge: '/vite.svg',
        vibrate: [200, 100, 200, 100, 200, 100, 200],
        requireInteraction: true,
        data: {
            dateOfArrival: Date.now(),
            primaryKey: '2'
        }
    };
    
    event.waitUntil(
        self.registration.showNotification(payload.title, options)
    );
});

self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    event.waitUntil(
        clients.matchAll({ type: 'window' }).then( windowClients => {
            for (var i = 0; i < windowClients.length; i++) {
                var client = windowClients[i];
                if (client.url.indexOf('/') !== -1 && 'focus' in client) {
                    return client.focus();
                }
            }
            if (clients.openWindow) {
                return clients.openWindow('/history.html');
            }
        })
    );
});
