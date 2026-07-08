const CACHE_NAME = "evidentia-shell-v38-mobile-header";
const STABLE_URL = "https://evidentia-ytra.onrender.com/";
const SHELL_ASSETS = [
  "./reset.html?v=20260708-stable-mobile",
  "./website.css?v=20260708-stable-mobile",
  "./styles.css?v=20260708-mobile-header",
  "./app.js?v=20260708-yolito-chat",
  "./manifest.webmanifest?v=20260708-stable-mobile",
  "./icon.svg?v=20260624-mirror-e",
  "./assets/icons/icon-192.png?v=20260708-stable-mobile",
  "./assets/icons/icon-512.png?v=20260708-stable-mobile",
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
  const fallbackResponse = () => {
    if (request.mode === "navigate") {
      return new Response(
        `<!doctype html>
        <html lang="es">
          <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Evidentia sin conexion</title>
            <style>
              body{margin:0;min-height:100vh;display:grid;place-items:center;background:#070809;color:#f5f2eb;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;padding:24px}
              main{max-width:440px}
              h1{font-size:24px;margin:0 0 12px}
              p{color:#b9b3aa;line-height:1.45;margin:0 0 16px}
              a{color:#070809;background:#f5f2eb;border:0;border-radius:8px;display:block;font-weight:700;margin:10px 0 0;padding:14px 16px;text-align:center;text-decoration:none;width:100%}
              .secondary{background:transparent;border:1px solid #3c414b;color:#f5f2eb}
            </style>
          </head>
          <body>
            <main>
              <h1>Evidentia no puede conectar</h1>
              <p>Este acceso temporal ha caducado. Usa el acceso estable de curso para trabajar sin depender del tunel del Mac.</p>
              <a href="${STABLE_URL}">Abrir Evidentia estable</a>
              <a class="secondary" href="./reset.html?v=20260708-stable-mobile">Limpiar este acceso antiguo</a>
            </main>
          </body>
        </html>`,
        { status: 503, headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store" } }
      );
    }
    return new Response("", { status: 503, statusText: "Evidentia offline" });
  };
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
        .then(response => response || fallbackResponse())
        .catch(() => fallbackResponse())
    );
    return;
  }

  event.respondWith(
    fetch(request, { cache: "no-store" })
      .then(response => {
        if (!response.ok || response.redirected) return response;
        const copy = response.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(request, copy));
        return response;
      })
      .catch(() => caches.match(request))
      .then(response => response || fallbackResponse())
  );
});
