# Onboarding — aplikacja dla hodowców zwierząt

Witaj w zespole. Ten dokument mówi, **co budujemy, jak postawić projekt lokalnie i kto za co odpowiada.**
Reguły kodu i bezpieczeństwa (które muszą być wspólne) są w `CLAUDE.md`. Model danych w `docs/MODEL_DANYCH.md`.

## Co budujemy

Profesjonalna aplikacja webowa dla **hodowców** (psy, konie, koty…) do prowadzenia profilu hodowli,
katalogu zwierząt z rodowodami i znajdowania par do rozrodu. **Nie jest to aplikacja randkowa** — ma
wyglądać jak narzędzie branżowe.

Zakres: czat WebSocket · edycja własnej hodowli, zwierząt i rodowodów · profile hodowli · przeglądanie
i filtrowanie zwierząt · lista hodowli z filtrami i paginacją · dopasowywanie po podobnych zwierzętach ·
weryfikacja rodowodu i podpinanie dokumentów (książeczki/PDF) · wyszukiwanie po mapie · współczynnik
inbredu · powiadomienia i ulubione.

## Stack (skrót)

React + Vite + TypeScript (frontend) · Flask + Flask-SocketIO (backend) · PostgreSQL · pełna tabela
w `CLAUDE.md`.

## Wymagania wstępne

- **Python 3.11+** i **Node.js 20+**
- **Git** + konto GitHub
- Konta (darmowe, zakładamy zespołowo): **Neon** (Postgres), **Render** (backend), **Vercel** (frontend),
  **Supabase** lub **Cloudinary** (pliki)
- **GitHub Student Pack** — daje m.in. darmową domenę `.me` (Namecheap) na rok. Potrzebujemy jej, żeby
  front i back stały na subdomenach jednej domeny (`app.…` / `api.…`) — inaczej cookie sesji jest
  blokowane jako third-party.

## Uruchomienie lokalne (po utworzeniu scaffoldingu)

```bash
# 1. Backend
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # uzupełnij wartości (patrz niżej)
flask db upgrade                 # utwórz schemat w bazie
flask run                        # http://localhost:5000

# 2. Frontend (w drugim terminalu)
cd frontend
npm install
cp .env.example .env             # ustaw adres API
npm run dev                      # http://localhost:5173
```

### Zmienne środowiskowe

`backend/.env`:
```
FLASK_APP=app
FLASK_DEBUG=1
SECRET_KEY=<długi losowy ciąg>
DATABASE_URL=postgresql://...        # connection string z Neon (lub lokalny Postgres)
FRONTEND_ORIGIN=http://localhost:5173
STORAGE_...=<klucze do Supabase/Cloudinary>
```

`frontend/.env`:
```
VITE_API_URL=http://localhost:5000
```

> Plików `.env` **nie commitujemy** — w repo trzymamy tylko `.env.example` z pustymi wartościami.

## Podział pracy (wstępny, do ustalenia na spotkaniu)

- **Osoba A — Auth & bezpieczeństwo:** rejestracja/logowanie (sesja httpOnly, Flask-Login, argon2),
  użytkownik, CRUD hodowli, wspólna warstwa walidacji Pydantic, CORS/rate limiting.
- **Osoba B — Zwierzęta & rodowody:** model zwierzęcia, graf rodowodu, dokumenty + weryfikacja,
  algorytm dopasowań i współczynnik inbredu.
- **Osoba C — Frontend rdzeń:** layout/design system, lista hodowli (filtry, paginacja), profile,
  przeglądanie i filtrowanie zwierząt, mapa (Leaflet).
- **Osoba D — Czas rzeczywisty:** czat WebSocket (Flask-SocketIO + klient), powiadomienia, ulubione,
  frontend czatu.

Warstwa wspólna (modele bazy, schematy Pydantic, typy TS) ustalana razem na początku, żeby się nie blokować.

## Workflow Git

- Pracujemy na branchach `feat/<obszar>-<opis>`, nigdy bezpośrednio na `main`.
- Każda zmiana wchodzi przez **Pull Request** z przeglądem przynajmniej jednej osoby.
- Małe, częste PR-y > jeden wielki.

## Zasady, o których pamiętamy od pierwszego dnia

- **Walidacja wejścia i bezpieczeństwo to priorytet oceny** — czytaj sekcję bezpieczeństwa w `CLAUDE.md`.
- **Rozumiej kod, który commitujesz.** Prowadzący będzie przepytywał z fragmentów aplikacji. Jeśli LLM coś
  wygenerował, a Ty nie rozumiesz — popraw prompt i kod, aż zrozumiesz.
- Kod czytelny, identyfikatory po angielsku, komentarze po polsku w nieoczywistych miejscach.
