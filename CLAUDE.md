# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **Status projektu:** faza startowa (greenfield). Repo jest jeszcze prawie puste — poniżej opisana jest
> **docelowa** architektura i konwencje uzgodnione przez zespół. Część komend zacznie działać dopiero po
> utworzeniu scaffoldingu (`backend/`, `frontend/`).

## Czym jest projekt

Aplikacja webowa dla **hodowców zwierząt** (psy, konie, koty itd.) do prowadzenia profilu hodowli,
katalogowania zwierząt z rodowodami i znajdowania par do rozrodu. To ma wyglądać i działać jak
**profesjonalne narzędzie branżowe** — nie jak aplikacja randkowa. Projekt akademicki, robiony przez
4-osobowy zespół.

Główne funkcje: czat WebSocket, edycja własnej hodowli i zwierząt, profile hodowli, przeglądanie
i filtrowanie zwierząt, lista hodowli z filtrami i paginacją, dopasowywanie po podobnych zwierzętach,
rodowody z weryfikacją i podpinaniem dokumentów, wyszukiwanie po mapie, współczynnik inbredu,
powiadomienia i ulubione.

## Stack technologiczny

| Warstwa | Technologia |
|---|---|
| Frontend | React + Vite + **TypeScript**, Tailwind + shadcn/ui, `socket.io-client`, Leaflet + OpenStreetMap |
| Backend | **Flask** + Flask-SocketIO, SQLAlchemy + Flask-Migrate (Alembic), **Pydantic v2** (walidacja), Flask-Login, argon2, Flask-Limiter |
| Baza | PostgreSQL (Neon na produkcji, lokalnie Postgres lub Docker) |
| Pliki | Supabase Storage lub Cloudinary (zdjęcia zwierząt, PDF rodowodów) — **nie trzymamy plików w bazie** |
| Hosting | Frontend → Vercel, Backend → Render, Baza → Neon |

## Architektura wysokopoziomowa

Frontend i backend to **dwa niezależne wdrożenia**, które komunikują się przez HTTPS (REST) i WSS (WebSocket):

```
Przeglądarka ──HTTPS REST──▶ Flask API (Render) ──▶ Postgres (Neon)
            ──WSS Socket──▶ Flask-SocketIO          │
                                                     └──▶ Storage plików (Supabase/Cloudinary)
```

- **REST API** obsługuje całą logikę CRUD i zapytania (lista hodowli, filtry, paginacja, dopasowania).
- **WebSocket (Flask-SocketIO)** obsługuje czat i powiadomienia w czasie rzeczywistym. Dlatego backend
  musi stać na hostingu z żywym procesem (Render) — serverless (np. funkcje Vercela) nie utrzyma
  stałego połączenia.
- **Uwierzytelnianie: sesja w cookie `httpOnly`** (Flask-Login). Ponieważ frontend i backend są na różnych
  domenach, cookie musi być `Secure`, `SameSite=None`, a CORS i klient Socket.IO muszą wysyłać credentials.
  **Docelowo front i back stoją na subdomenach tej samej domeny** (`app.…` / `api.…`), żeby cookie było
  first-party — inaczej przeglądarki blokują je jako third-party. Konfigurację CORS/cookie zmieniaj
  świadomie; to element oceniany za bezpieczeństwo.
- **Rodowód** jest grafem: model `Animal` odwołuje się sam do siebie przez `sire_id` (ojciec) i `dam_id`
  (matka). Przeglądanie przodków i liczenie inbredu = trawersowanie tego grafu (patrz `docs/MODEL_DANYCH.md`).

## Docelowa struktura repo

```
backend/    Flask API + Socket.IO, modele SQLAlchemy, schematy Pydantic, migracje Alembic
frontend/   React + Vite + TS (komponenty, strony, klient API i Socket.IO)
docs/        Dokumentacja projektowa (model danych, decyzje)
```

## Komendy (docelowe — po utworzeniu scaffoldingu)

```bash
# Backend (z katalogu backend/, w aktywnym venv)
pip install -r requirements.txt
flask db upgrade            # zastosuj migracje
flask db migrate -m "opis"  # wygeneruj migrację po zmianie modeli
flask run                   # dev server (REST + Socket.IO)
pytest                      # testy
pytest tests/test_x.py::test_y   # pojedynczy test

# Frontend (z katalogu frontend/)
npm install
npm run dev                 # dev server Vite
npm run build               # build produkcyjny
npm run lint                # ESLint
```

## Konwencje kodu

- **Czytelność ponad spryt.** Kod ma być zrozumiały dla każdego z 4 członków zespołu — każdy może zostać
  przepytany z dowolnego fragmentu. Unikaj „magii" i nieoczywistych skrótów.
- **Identyfikatory po angielsku** (zmienne, funkcje, klasy, tabele, pola) — standard.
- **Komentarze po polsku tam, gdzie wyjaśniają „dlaczego"** lub nieoczywistą logikę domenową (np. wzór na
  inbred, reguły dopasowania). Nie komentuj rzeczy oczywistych z kodu.
- **TypeScript bez `any`.** Typuj odpowiedzi API i propsy. Typy współdzielonych encji trzymaj w jednym miejscu.
- Backend: **endpoint → walidacja Pydantic → logika (serwis) → ORM**. Trzymaj logikę domenową poza handlerami
  tras, żeby dało się ją testować i ponownie używać.

## Twarde reguły bezpieczeństwa i walidacji (priorytet oceny)

Prowadzący ocenia w szczególności **walidację danych wejściowych** i bezpieczeństwo. Bezwzględnie:

1. **Każdy** endpoint waliduje wejście schematem **Pydantic** zanim cokolwiek trafi do logiki/bazy.
   Nigdy nie ufaj danym z klienta.
2. **Tylko ORM (SQLAlchemy)**, zero sklejanego ręcznie SQL — chroni przed SQL injection.
3. **Autoryzacja właściciela:** użytkownik modyfikuje wyłącznie własne zasoby (np. `farm.owner_id ==
   current_user.id`). Sprawdzaj to przy KAŻDEJ operacji zapisu/edycji/usuwania, nie tylko w UI.
4. **Hasła** hashowane argon2; nigdy nie logowane ani nie zwracane w API.
5. **Upload plików:** waliduj typ MIME i rozmiar (zdjęcia, PDF rodowodów); nie ufaj rozszerzeniu z nazwy.
6. **Rate limiting** (Flask-Limiter) na logowaniu i rejestracji.
7. **CORS** ograniczony do znanych originów frontendu, z `credentials`. Cookie sesji `httpOnly` + `Secure`.
8. Nie zwracaj w API danych wrażliwych ani pól, których frontend nie potrzebuje.

## Reguły domenowe

- **Inbred:** przed zasugerowaniem pary licz pokrewieństwo kandydatów (oczekiwany współczynnik inbredu
  potomstwa) z grafu rodowodu i ostrzegaj/odfiltrowuj zbyt spokrewnione zwierzęta. Wzór i podejście:
  `docs/MODEL_DANYCH.md`.
- **Dopasowania** to algorytm (gatunek, rasa, płeć przeciwna, dostępność do rozrodu, bliskość na mapie,
  niski inbred) — nie osobny workflow akceptacji (nie jest w zakresie).
- **Mapa/odległość:** filtruj po promieniu na podstawie `latitude`/`longitude` hodowli.

## Czego nie robić

- Nie nadawać aplikacji estetyki/UX aplikacji randkowej (swipe'y itp.) — to narzędzie dla hodowców.
- Nie hostować backendu z WebSocketem na serverless (Vercel) — użyj Render.
- Nie dodawać funkcji spoza ustalonego zakresu bez uzgodnienia (ocena = realizacja ustalonych punktów).
- Nie obchodzić walidacji ani sprawdzania właściciela „na szybko" — to wprost obniża ocenę.
