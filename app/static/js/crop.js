/* Kadrowanie zdjęć przy uploadzie (Lab 4/7 — client-side JS + Fetch/FormData).
 *
 * Po co: w całej aplikacji zdjęcia mają proporcje 3:2. Zamiast pozwalać, żeby
 * serwer ślepo przyciął wgrany plik (i „uciął głowę psu"), pokazujemy proste
 * okno kadrowania — użytkownik sam decyduje, co znajdzie się w kadrze. Wynik
 * jest już w 3:2, więc na kartach nic się widocznie nie ucina.
 *
 * Bez build pipeline'u: biblioteka Cropper.js z CDN (jak Leaflet), reszta to
 * czysty JS. Działa progresywnie — gdy JS jest wyłączony, leci surowy plik,
 * a walidacja typu/rozmiaru i tak jest po stronie serwera (services/uploads).
 */
(function () {
  "use strict";

  // Parsuje data-crop: "3:2", "3/2" albo liczbę "1.5" → stosunek szer/wys.
  function parseRatio(value) {
    if (!value) return 3 / 2;
    const m = value.match(/^(\d+(?:\.\d+)?)\s*[:/]\s*(\d+(?:\.\d+)?)$/);
    if (m) return parseFloat(m[1]) / parseFloat(m[2]);
    const n = parseFloat(value);
    return Number.isFinite(n) && n > 0 ? n : 3 / 2;
  }

  // Pojedynczy, współdzielony overlay — budujemy raz, leniwie.
  let overlay = null;
  let imageEl = null;
  let cropper = null;
  let activeInput = null;
  let objectUrl = null;

  function buildOverlay() {
    overlay = document.createElement("div");
    overlay.className = "crop-overlay";
    overlay.hidden = true;
    overlay.innerHTML = `
      <div class="crop-dialog" role="dialog" aria-modal="true" aria-label="Kadrowanie zdjęcia">
        <div class="crop-head">
          <strong>Skadruj zdjęcie</strong>
          <span class="crop-hint">Proporcje 3:2 — przeciągnij i przybliż, żeby wybrać kadr.</span>
        </div>
        <div class="crop-stage"><img alt="" /></div>
        <div class="crop-actions">
          <button type="button" class="btn btn-light" data-crop-cancel>Anuluj</button>
          <button type="button" class="btn btn-primary" data-crop-confirm>Przytnij i użyj</button>
        </div>
      </div>`;
    document.body.appendChild(overlay);
    imageEl = overlay.querySelector("img");

    overlay.querySelector("[data-crop-cancel]").addEventListener("click", cancel);
    overlay.querySelector("[data-crop-confirm]").addEventListener("click", confirm);
    overlay.addEventListener("click", function (e) {
      if (e.target === overlay) cancel();
    });
    document.addEventListener("keydown", function (e) {
      if (!overlay.hidden && e.key === "Escape") cancel();
    });
  }

  function open(input, file, ratio) {
    if (!overlay) buildOverlay();
    activeInput = input;
    if (objectUrl) URL.revokeObjectURL(objectUrl);
    objectUrl = URL.createObjectURL(file);

    imageEl.onload = function () {
      if (cropper) cropper.destroy();
      // viewMode 1 — kadr nie wychodzi poza zdjęcie; autoCropArea — od razu duży kadr.
      cropper = new Cropper(imageEl, {
        aspectRatio: ratio,
        viewMode: 1,
        autoCropArea: 1,
        background: false,
        responsive: true,
      });
    };
    imageEl.src = objectUrl;
    overlay.hidden = false;
    document.body.style.overflow = "hidden";
  }

  function close() {
    if (cropper) {
      cropper.destroy();
      cropper = null;
    }
    if (objectUrl) {
      URL.revokeObjectURL(objectUrl);
      objectUrl = null;
    }
    if (overlay) overlay.hidden = true;
    document.body.style.overflow = "";
  }

  function cancel() {
    // Rezygnacja = czyścimy input, żeby nie poszedł nieskadrowany plik.
    if (activeInput) activeInput.value = "";
    activeInput = null;
    close();
  }

  function confirm() {
    if (!cropper || !activeInput) return close();
    const input = activeInput;
    // Eksport do 1200×800 (3:2) — spójne z zaleceniami dla zdjęć stockowych.
    const canvas = cropper.getCroppedCanvas({
      width: 1200,
      height: 800,
      imageSmoothingQuality: "high",
    });
    canvas.toBlob(
      function (blob) {
        if (!blob) return cancel();
        const cropped = new File([blob], "photo.jpg", { type: "image/jpeg" });
        // DataTransfer pozwala podmienić zawartość <input type=file> programowo.
        const dt = new DataTransfer();
        dt.items.add(cropped);
        input.files = dt.files;
        showPreview(input, canvas.toDataURL("image/jpeg", 0.9));
        activeInput = null;
        close();
      },
      "image/jpeg",
      0.9
    );
  }

  // Miniatura tego, co faktycznie poleci na serwer — wstawiana pod inputem.
  function showPreview(input, dataUrl) {
    let preview = input.parentNode.querySelector(".crop-preview");
    if (!preview) {
      preview = document.createElement("img");
      preview.className = "crop-preview";
      preview.alt = "Podgląd kadru";
      input.parentNode.insertBefore(preview, input.nextSibling);
    }
    preview.src = dataUrl;
  }

  function handleChange(e) {
    const input = e.target;
    const file = input.files && input.files[0];
    if (!file) return;
    // Kadrujemy tylko obrazki. Inne pliki (np. PDF) puszczamy bez zmian.
    if (!file.type.startsWith("image/")) return;
    if (typeof window.Cropper === "undefined") return; // brak CDN → zostaw surowy plik
    open(input, file, parseRatio(input.dataset.crop));
  }

  document.addEventListener("DOMContentLoaded", function () {
    document
      .querySelectorAll("input[type=file][data-crop]")
      .forEach(function (input) {
        input.addEventListener("change", handleChange);
      });
  });
})();
