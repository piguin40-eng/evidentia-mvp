const CACHE_NAME = "evidentia-shell-v10-roi-intel";
const SHELL_ASSETS = [
  "./",
  "./index.html",
  "./website.html",
  "./website.css?v=20260617-roi-intel",
  "./styles.css?v=20260617-roi-intel",
  "./app.js?v=20260617-roi-intel",
  "./manifest.webmanifest",
  "./icon.svg",
  "./assets/evidentia/evidentia-hero.mp4?v=20260617-roi-intel",
  "./assets/evidentia/evidentia-hero-poster.jpg?v=20260617-roi-intel"
];

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(SHELL_ASSETS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", event => {
  const request = event.request;
  if (request.method !== "GET") return;
  event.respondWith(
    fetch(request)
      .then(response => {
        const copy = response.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(request, copy));
        return response;
      })
      .catch(() => caches.match(request).then(cached => cached || caches.match("./index.html")))
  );
});
