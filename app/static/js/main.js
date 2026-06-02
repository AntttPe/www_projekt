// Wspólny JS — podpięcie globalnego Socket.IO i CSRF helpera.

(() => {
  // CSRF token z meta tagu — dołączany do wywołań fetch() jako nagłówek.
  const meta = document.querySelector('meta[name="csrf-token"]');
  window.CSRF_TOKEN = meta ? meta.content : "";

  // Wrapper na fetch, który automatycznie dorzuca CSRF do POST/PUT/PATCH/DELETE.
  window.apiFetch = async (url, options = {}) => {
    const opts = Object.assign({ credentials: "same-origin" }, options);
    const headers = new Headers(opts.headers || {});
    headers.set("Accept", "application/json");
    if (!headers.has("Content-Type") && opts.body) headers.set("Content-Type", "application/json");
    if (opts.method && !["GET", "HEAD"].includes(opts.method.toUpperCase())) {
      headers.set("X-CSRFToken", window.CSRF_TOKEN);
    }
    opts.headers = headers;
    return fetch(url, opts);
  };

  // Powiadomienia w czasie rzeczywistym: jeśli użytkownik jest zalogowany,
  // podłączamy do socketu i nasłuchujemy zdarzenia "notification".
  // (Globalny socket — pojedynczy dla całej zakładki.)
  if (typeof io !== "undefined") {
    window.appSocket = io({ transports: ["websocket", "polling"] });
    window.appSocket.on("notification", (data) => {
      // W przyszłości: toast w prawym dolnym rogu; na razie tylko log.
      console.log("Nowe powiadomienie:", data);
    });
  }
})();
