// Service worker: ដាក់តែ install/activate ប៉ុណ្ណោះ (គ្មាន fetch handler ដើម្បីកុំឲ្យ Chrome ព្រមាន no-op)
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (e) => e.waitUntil(self.clients.claim()));
