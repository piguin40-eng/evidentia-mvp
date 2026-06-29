const CACHE_NAME = "evidentia-shell-v32-rag-refresh";
const SHELL_ASSETS = [
  "./index.html?v=20260629-rag-refresh",
  "./reset.html?v=20260622-mobile-reset",
  "./website.html?v=20260622-good-web-restore",
  "./website.css?v=20260622-good-web-restore",
  "./styles.css?v=20260629-rag-refresh",
  "./app.js?v=20260629-rag-refresh",
  "./manifest.webmanifest?v=20260628-mobile-app",
  "./icon.svg?v=20260624-mirror-e",
  "./assets/icons/icon-192.png?v=20260628-mobile-app",
  "./assets/icons/icon-512.png?v=20260628-mobile-app",
  "./assets/evidentia/evidentia-reference-hero.mp4?v=20260618-reference-video",
  "./assets/evidentia/evidentia-reference-hero-poster.jpg?v=20260618-reference-video"
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
  const url = new URL(request.url);
  const isFreshDocument =
    request.mode === "navigate" ||
    url.pathname === "/" ||
    url.pathname.endsWith("/index.html") ||
    url.pathname.endsWith("/website.html") ||
    url.pathname.endsWith("/reset.html") ||
    url.pathname.endsWith("/manifest.webmanifest") ||
    url.pathname.endsWith("/sw.js");

  if (isFreshDocument) {
    event.respondWith(
      fetch(request, { cache: "no-store" })
        .catch(() => caches.match(request).then(cached => cached || caches.match("./index.html?v=20260629-rag-refresh")))
    );
    return;
  }

  event.respondWith(
    fetch(request)
      .then(response => {
        const copy = response.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(request, copy));
        return response;
      })
      .catch(() => caches.match(request).then(cached => cached || caches.match("./index.html?v=20260629-rag-refresh")))
  );
});
