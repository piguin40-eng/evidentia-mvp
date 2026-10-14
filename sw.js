// Course node: network only. Never cache knowledge or redirect to another node.
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", event => event.waitUntil(self.clients.claim()));
self.addEventListener("fetch", event => { if (event.request.method === "GET") event.respondWith(fetch(event.request, {cache:"no-store"})); });
