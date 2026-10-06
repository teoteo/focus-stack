// Service worker minimale: rende l'app installabile (Safari › File › Aggiungi al Dock)
// e mette in cache l'interfaccia. Le API passano sempre dalla rete.
const CACHE = "focus-stack-v3";
const SHELL = ["/", "/index.html", "/style.css", "/app.js", "/icon.svg", "/manifest.webmanifest", "/viewer.html", "/viewer.js"];

self.addEventListener("install", (e) => e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting())));
self.addEventListener("activate", (e) => e.waitUntil(
  caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim())));
self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.pathname.startsWith("/api") || url.pathname === "/ws") return;
  // network-first: l'interfaccia è sempre aggiornata quando il server è attivo
  e.respondWith(fetch(e.request).then((r) => {
    const copy = r.clone();
    caches.open(CACHE).then((c) => c.put(e.request, copy));
    return r;
  }).catch(() => caches.match(e.request)));
});
