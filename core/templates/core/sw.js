/*
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: core/templates/core/sw.js
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 18/06/2026 13:20
* LOG DE ALTERAÇÕES:
* - 18/06/2026 13:20: Auditoria e padronização global (Goal)
*/
const CACHE_NAME = 'pve-intranet-v1';
const ASSETS_TO_CACHE = [
  '/',
  '/manifest.json',
  '/static/core/img/pwa-icon-192.png',
  '/static/core/img/pwa-icon-512.png',
  '/static/core/img/logo.jpg'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        return cache.addAll(ASSETS_TO_CACHE);
      })
  );
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.filter(name => name !== CACHE_NAME)
          .map(name => caches.delete(name))
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;

  // Estratégia: Network First, caindo para Cache (Ideal para intranet interativa)
  event.respondWith(
    fetch(event.request)
      .then(response => {
        // Se a resposta for boa, clonamos e guardamos no cache
        if (response.status === 200) {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then(cache => {
            cache.put(event.request, responseClone);
          });
        }
        return response;
      })
      .catch(() => {
        // Offline ou erro de rede, tenta pegar do cache
        return caches.match(event.request);
      })
  );
});
