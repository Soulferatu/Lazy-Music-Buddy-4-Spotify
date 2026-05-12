if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/static/service-worker.js").catch(() => {
      // Local development can still continue when service worker registration fails.
    });
  });
}
