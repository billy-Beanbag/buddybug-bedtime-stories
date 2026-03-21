const SHELL_CACHE = "buddybug-shell-v1";
const RUNTIME_CACHE = "buddybug-runtime-v1";
const PACKAGE_CACHE = "buddybug-package-v1";
const OFFLINE_RESOURCE_CACHE = "buddybug-offline-resources-v1";
const ALL_CACHES = [SHELL_CACHE, RUNTIME_CACHE, PACKAGE_CACHE, OFFLINE_RESOURCE_CACHE];

const SHELL_URLS = ["/", "/manifest.json", "/icons/icon-192.svg", "/icons/icon-512.svg", "/icons/apple-touch-icon.svg"];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(SHELL_CACHE).then((cache) => cache.addAll(SHELL_URLS)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((key) => !ALL_CACHES.includes(key)).map((key) => caches.delete(key))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") {
    return;
  }

  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin) {
    return;
  }

  if (url.pathname.startsWith("/mock-assets/downloads/")) {
    event.respondWith(cacheFirst(event.request, PACKAGE_CACHE));
    return;
  }

  if (event.request.mode === "navigate") {
    event.respondWith(networkFirst(event.request, SHELL_CACHE, "/"));
    return;
  }

  if (
    url.pathname.startsWith("/_next/static/") ||
    url.pathname.startsWith("/icons/") ||
    url.pathname === "/manifest.json" ||
    event.request.destination === "script" ||
    event.request.destination === "style" ||
    event.request.destination === "font"
  ) {
    event.respondWith(staleWhileRevalidate(event.request, RUNTIME_CACHE));
    return;
  }

  if (event.request.destination === "image" || event.request.destination === "audio") {
    event.respondWith(cacheFirst(event.request, OFFLINE_RESOURCE_CACHE));
  }
});

async function cacheFirst(request, cacheName) {
  const cached = await caches.match(request);
  if (cached) {
    return cached;
  }
  const response = await fetch(request);
  if (response && response.ok) {
    const cache = await caches.open(cacheName);
    cache.put(request, response.clone());
  }
  return response;
}

async function networkFirst(request, cacheName, fallbackUrl) {
  try {
    const response = await fetch(request);
    if (response && response.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    const cached = await caches.match(request);
    if (cached) {
      return cached;
    }
    return caches.match(fallbackUrl);
  }
}

async function staleWhileRevalidate(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);
  const networkPromise = fetch(request)
    .then((response) => {
      if (response && response.ok) {
        cache.put(request, response.clone());
      }
      return response;
    })
    .catch(() => null);

  if (cached) {
    return cached;
  }

  const response = await networkPromise;
  if (response) {
    return response;
  }
  return new Response("Offline", { status: 503, statusText: "Offline" });
}
