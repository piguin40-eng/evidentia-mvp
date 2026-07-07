const CACHE_NAME = "evidentia-shell-v35-command-deck";
const SHELL_ASSETS = [
  "./reset.html?v=20260629-mobile-shell",
  "./website.css?v=20260702-operating-contract",
  "./styles.css?v=20260702-command-deck",
  "./app.js?v=20260702-command-deck",
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
              a{color:#f5f2eb}
            </style>
          </head>
          <body>
            <main>
              <h1>Evidentia no puede conectar</h1>
              <p>El nodo local o el enlace movil temporal no esta disponible ahora mismo. Abre el enlace movil mas reciente o reinicia el acceso movil desde el Mac.</p>
              <p><a href="./reset.html">Limpiar acceso local</a></p>
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
        .catch(() => caches.match(request))
        .then(response => response || fallbackResponse())
    );
    return;
  }

  event.respondWith(
    fetch(request)
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
