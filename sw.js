// 21/08/2026 — Service Worker mínimo, para que la app sea instalable como PWA de verdad
// (ícono propio, ventana sin barra de navegador) en Android y en computador.
//
// DISEÑO DELIBERADAMENTE CONSERVADOR. Este proyecto ya sufrió varios días de bugs reales por
// datos que quedaban en caché sin que nadie se enterara (ver contexto-proyecto.md: version.json,
// horas del horario, número de cuenta — todos por el mismo patrón: algo se guardó y no se volvió
// a leer fresco). Un Service Worker mal diseñado es exactamente la misma trampa, pero a mayor
// escala — por eso este SOLO hace dos cosas, nada más:
//   1) Cuando se abre la página principal, intenta SIEMPRE la red primero. Solo si falla de
//      verdad (sin internet) muestra la última copia guardada, en vez de una pantalla de error.
//   2) Todo lo demás (llamadas al Apps Script, version.json, fuentes, jsPDF/html2canvas) pasa de
//      largo sin tocarlo — nunca se cachea, nunca se intercepta. Ver el filtro `mode==='navigate'`
//      más abajo: si no es la navegación de la página principal, este archivo ni se entera.
const CACHE_NAME = 'andersson-shell-v1';
const SHELL_URLS = ['/', '/manifest.json', '/icon192.png', '/icon512.png'];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL_URLS)).catch(() => {})
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  // Solo se intercepta la NAVEGACIÓN a la página principal — nunca las llamadas que la app hace
  // por su cuenta (gasCall al Apps Script, version.json, fuentes, jsPDF/html2canvas). Esas siguen
  // yendo directo a la red, exactamente igual que si este archivo no existiera.
  if (req.method !== 'GET' || req.mode !== 'navigate') return;

  event.respondWith(
    fetch(req)
      .then((res) => {
        caches.open(CACHE_NAME).then((cache) => cache.put('/', res.clone())).catch(() => {});
        return res;
      })
      .catch(() => caches.match('/').then((cached) => cached || Response.error()))
  );
});
