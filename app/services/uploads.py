"""Walidacja i zapis przesłanych plików (zdjęcia hodowli/zwierząt, PDF rodowodów).

Lab 9 — świadome przeciwwagi dla typowych podatności uploadu:

- **Nie ufamy rozszerzeniu z nazwy.** Typ rozpoznajemy po „magicznych bajtach"
  (sniffing zawartości). Plik `wirus.jpg`, który w środku jest czymś innym,
  zostanie odrzucony.
- **Limit rozmiaru per plik** (poza globalnym MAX_CONTENT_LENGTH) — ochrona
  przed DoS dużymi uploadami.
- **Nazwę pliku generujemy sami** (uuid). Użytkownik NIE wpływa na ścieżkę
  zapisu → brak path traversal / LFI (moduł `lfi.py` z Lab 9).
- Pliki trafiają do whitelistowanego katalogu i są serwowane wyłącznie przez
  kontrolowaną trasę (`main.media`), nigdy przez `open()` po ścieżce od klienta.
"""

from __future__ import annotations

import os
import uuid

from flask import current_app
from werkzeug.datastructures import FileStorage

# Dozwolone typy MIME → rozszerzenie, które NADAJEMY przy zapisie (nie bierzemy z nazwy).
IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
PDF_TYPES = {"application/pdf": ".pdf"}

MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB
MAX_PDF_BYTES = 10 * 1024 * 1024  # 10 MB

# Whitelist katalogów (podkatalogi w UPLOAD_FOLDER). Trasa serwująca też ich pilnuje.
KIND_PHOTOS = "photos"
KIND_DOCUMENTS = "documents"
ALLOWED_KINDS = {KIND_PHOTOS, KIND_DOCUMENTS}

# Rozszerzenia akceptowane w lokalnym katalogu „dobrych" zdjęć (static/img/stock/<gatunek>).
_STOCK_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
_stock_cache: dict[str, list[str]] = {}


def stock_photos_for(species: str) -> list[str]:
    """Lista plików w static/img/stock/<gatunek>/ (posortowana, deterministyczna).

    Używana przez makro `photo_plate` jako źródło zdjęć przed fallbackiem na
    loremflickr. Wynik cache'ujemy poza trybem debug — w dev wystarczy wrzucić
    pliki do folderu i odświeżyć stronę, w produkcji liczymy listę raz.
    """
    if not current_app.debug and species in _stock_cache:
        return _stock_cache[species]

    folder = os.path.join(current_app.static_folder, "img", "stock", species)
    names: list[str] = []
    if os.path.isdir(folder):
        names = sorted(
            f
            for f in os.listdir(folder)
            if not f.startswith(".") and os.path.splitext(f)[1].lower() in _STOCK_EXTENSIONS
        )
    _stock_cache[species] = names
    return names


class UploadError(ValueError):
    """Błąd walidacji pliku. Komunikat jest przyjazny — trafia wprost do `flash`."""


def _sniff_mime(head: bytes) -> str | None:
    """Rozpoznaje typ po sygnaturze (magic bytes), nie po rozszerzeniu."""
    if head.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image/webp"
    if head.startswith(b"%PDF-"):
        return "application/pdf"
    return None


def _upload_root() -> str:
    return current_app.config["UPLOAD_FOLDER"]


def save_upload(file: FileStorage | None, *, kind: str) -> str | None:
    """Waliduje i zapisuje plik.

    Zwraca wygenerowaną nazwę (do zapisania w bazie) albo `None`, gdy nic nie
    przesłano. Rzuca `UploadError` przy pliku niespełniającym reguł.
    """
    if file is None or not file.filename:
        return None  # pole zostawione puste — to nie błąd

    if kind == KIND_PHOTOS:
        allowed, max_bytes, human = IMAGE_TYPES, MAX_IMAGE_BYTES, "JPG, PNG lub WebP"
    elif kind == KIND_DOCUMENTS:
        allowed, max_bytes, human = PDF_TYPES, MAX_PDF_BYTES, "PDF"
    else:
        raise UploadError("Nieobsługiwany typ zasobu.")

    # Rozmiar liczymy ze strumienia, bez wczytywania całości do pamięci.
    stream = file.stream
    stream.seek(0, os.SEEK_END)
    size = stream.tell()
    stream.seek(0)
    if size == 0:
        raise UploadError("Przesłany plik jest pusty.")
    if size > max_bytes:
        raise UploadError(f"Plik za duży — maksymalnie {max_bytes // (1024 * 1024)} MB.")

    # Typ wyłącznie po zawartości.
    mime = _sniff_mime(stream.read(16))
    stream.seek(0)
    if mime not in allowed:
        raise UploadError(f"Niedozwolony typ pliku — wymagany {human}.")

    # Nazwę generujemy my → klient nie kontroluje ścieżki (anty path-traversal).
    name = f"{uuid.uuid4().hex}{allowed[mime]}"
    target_dir = os.path.join(_upload_root(), kind)
    os.makedirs(target_dir, exist_ok=True)
    file.save(os.path.join(target_dir, name))
    return name


def delete_upload(name: str | None, *, kind: str) -> None:
    """Usuwa stary plik (np. przy podmianie zdjęcia). Odporna na ścieżki."""
    if not name or kind not in ALLOWED_KINDS:
        return
    # Akceptujemy wyłącznie samą nazwę pliku — żadnych separatorów ścieżek.
    if "/" in name or "\\" in name or name in {".", ".."}:
        return
    path = os.path.join(_upload_root(), kind, name)
    if os.path.isfile(path):
        os.remove(path)
