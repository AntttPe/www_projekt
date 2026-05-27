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

**Wszystko serwowane przez Flaska** (jeden codebase, jeden deployment):

- **Frontend:** Jinja2 + Bootstrap 5 + Alpine.js + Fetch API + Socket.IO client + Leaflet (mapa)
- **Backend:** Flask v3 + Flask-SocketIO + SQLAlchemy + Flask-Migrate + Flask-Login + Pydantic + Swagger
- **Baza:** **SQLite** (plik w repo lokalnie, w `~/data/tindog.db` na AGH lab; ten sam silnik co Lab 9)
- **Pliki (zdjęcia, PDF rodowodów):** Supabase Storage lub Cloudinary (HTTPS outbound); fallback lokalny katalog `~/uploads/` na AGH lab, jeśli outbound HTTPS blocked
- **Hosting:** **AGH lab** (`*.lab.kis.agh.edu.pl`, „Proxy to standalone app server") — pełna tabela
  z numerami labów jest w `CLAUDE.md`.

## Wymagania wstępne

- **Python 3.11+**, `pip`, `venv`
- **Git** + konto GitHub
- Konto **Supabase** lub **Cloudinary** (storage plików) — opcjonalnie; klucze do współdzielonego `.env`
  od osoby A. Jeśli AGH blokuje HTTPS outbound, używamy lokalnego katalogu na AGH lab.
- Konto **AGH lab** (każdy ma swoje); deployment idzie na konto wskazanej osoby (np. `antttpe`)
- **Baza:** nic nie instalujesz. SQLite to plik tworzony automatycznie przez Alembic przy `flask db upgrade`.

## Uruchomienie lokalne (po utworzeniu scaffoldingu)

```bash
python -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt    # runtime + ruff/pytest/pre-commit
pre-commit install                     # hooki: ruff, format, trailing-whitespace
cp .env.example .env                   # uzupełnij SECRET_KEY (patrz niżej)
python wsgi.py                         # http://localhost:5001 (REST + szablony + Socket.IO)
                                        # 5001 zamiast 5000, bo macOS AirPlay Receiver zajmuje 5000

# Po dodaniu pierwszych modeli SQLAlchemy:
# flask db init                        (jednorazowo, twórca migracji)
# flask db migrate -m "init"           (po każdej zmianie modeli)
# flask db upgrade                     (każdy w zespole po pull, jeśli pojawiły się nowe migracje)
```

Tyle. **Nie ma osobnego serwera frontu** — Flask serwuje wszystko. Używamy `python wsgi.py`,
a nie `flask run`, bo `flask run` (Werkzeug) nie obsługuje WebSocketów poprawnie.

### Zmienne środowiskowe

`.env`:
```
FLASK_APP=wsgi:app
FLASK_DEBUG=1
SECRET_KEY=<długi losowy ciąg>
DATABASE_URL=sqlite:///instance/tindog.db          # lokalnie; na AGH lab: sqlite:////home/<login>/data/tindog.db
STORAGE_PROVIDER=local                              # albo supabase / cloudinary
# Jeśli storage zewnętrzny:
# SUPABASE_URL=...
# SUPABASE_SERVICE_KEY=...
```

> Plików `.env` **nie commitujemy** — w repo trzymamy tylko `.env.example` z pustymi wartościami.

## Podział pracy (wstępny, do ustalenia na spotkaniu)

- **Osoba A — Auth, bezpieczeństwo, fundament:** rejestracja/logowanie (sesja httpOnly, Flask-Login,
  argon2), użytkownik, CRUD hodowli, wspólna warstwa walidacji Pydantic, CSRF, rate limiting, konfiguracja
  Swaggera.
- **Osoba B — Zwierzęta, rodowody, logika domenowa:** model zwierzęcia, graf rodowodu, dokumenty +
  weryfikacja, algorytm dopasowań i współczynnik inbredu.
- **Osoba C — Widoki i wygląd:** szablony Jinja2, własna paleta na bazie Bootstrap, lista hodowli
  (filtry, paginacja), profile hodowli i zwierząt, mapa (Leaflet), strona startowa.
- **Osoba D — Czas rzeczywisty i interakcje:** czat Flask-SocketIO + klient Socket.IO, powiadomienia,
  ulubione, interaktywne kawałki Alpine.js (filtry, modale, formularze AJAX-owe).

Warstwa wspólna (modele bazy, schematy Pydantic, layout Jinja2) ustalana razem na początku, żeby się
nie blokować.

## Workflow Git

- Pracujemy na branchach `feat/<obszar>-<opis>`, nigdy bezpośrednio na `main`.
- Każda zmiana wchodzi przez **Pull Request** z przeglądem przynajmniej jednej osoby.
- Małe, częste PR-y > jeden wielki.

## Deployment na AGH lab (skrót)

Repo na AGH lab klonujemy do `~/tindog/`. Demo z Lab 9 w `~/app/` zostaje nietknięte (referencja
przy obronie). Na socket `~/app.sock` słucha tylko jeden gunicorn na raz — jak deployujemy nasz,
demo „schodzi z anteny", i odwrotnie.

1. Wybrać konfigurację **„Proxy to standalone app server"** na panelu AGH lab.
2. `ssh <login>@lab.kis.agh.edu.pl`; pierwszy raz: `git clone <repo> ~/tindog && cd ~/tindog && python -m venv .venv`.
3. `source .venv/bin/activate && pip install -r requirements.txt && flask db upgrade`.
4. `rsync -a app/static/ ~/public_html/` — statyki dla proxy uczelni.
5. Wystartować gunicorna słuchającego na `~/app.sock`:
   ```bash
   gunicorn -k gevent -w 1 --bind unix:$HOME/app.sock wsgi:app
   ```
6. Otworzyć `https://<login>.lab.kis.agh.edu.pl` i sprawdzić, czy Socket.IO łączy się przez WS
   (DevTools → Network → WS). Jeśli proxy nie przepuszcza upgrade, klient automatycznie spadnie na
   long-polling — czat działa tak czy inaczej.

## Zasady, o których pamiętamy od pierwszego dnia

- **Walidacja wejścia i bezpieczeństwo to priorytet oceny** (Lab 9) — czytaj sekcję bezpieczeństwa
  w `CLAUDE.md`.
- **Rozumiej kod, który commitujesz.** Prowadzący będzie przepytywał z fragmentów aplikacji. Jeśli LLM coś
  wygenerował, a Ty nie rozumiesz — popraw prompt i kod, aż zrozumiesz. Stack jest celowo dobrany
  pod programy labów, żeby każdy fragment dało się obronić.
- Kod czytelny, identyfikatory po angielsku, komentarze po polsku w nieoczywistych miejscach.
