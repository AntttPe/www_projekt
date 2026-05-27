# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **Status projektu:** faza startowa (greenfield). Repo jest jeszcze prawie puste — poniżej opisana jest
> **docelowa** architektura i konwencje uzgodnione przez zespół. Część komend zacznie działać dopiero po
> utworzeniu scaffoldingu Flaska.

## Czym jest projekt

Aplikacja webowa dla **hodowców zwierząt** (psy, konie, koty itd.) do prowadzenia profilu hodowli,
katalogowania zwierząt z rodowodami i znajdowania par do rozrodu. To ma wyglądać i działać jak
**profesjonalne narzędzie branżowe** — nie jak aplikacja randkowa. Projekt akademicki, robiony przez
4-osobowy zespół.

Główne funkcje: czat WebSocket, edycja własnej hodowli i zwierząt, profile hodowli, przeglądanie
i filtrowanie zwierząt, lista hodowli z filtrami i paginacją, dopasowywanie po podobnych zwierzętach,
rodowody z weryfikacją i podpinaniem dokumentów, wyszukiwanie po mapie, współczynnik inbredu,
powiadomienia i ulubione.

## Stack technologiczny (zgodny z programem laboratoriów)

Każda warstwa odpowiada laboratoriom kursu — to ułatwia obronę kodu w trakcie przepytania.

| Warstwa | Technologia | Powiązany lab |
|---|---|---|
| Szablony i wygląd | **Jinja2** (renderowane przez Flask) + **Bootstrap 5** | Lab 2, 3 |
| Reaktywność i AJAX | **Alpine.js** + **Fetch API** | Lab 3, 4, 7 |
| Czas rzeczywisty | **Socket.IO client** ↔ **Flask-SocketIO** | Lab 8 |
| Backend | **Flask v3** + SQLAlchemy + Flask-Migrate + Flask-Login | Lab 5 |
| Dokumentacja API | **Swagger** (`flasgger` / `spectree` / `flask-smorest` — narzędzie do potwierdzenia z Lab 6) | Lab 6 |
| Walidacja | **Pydantic v2** (lub marshmallow, zgodnie z Lab 6) | Lab 6, 9 |
| Bezpieczeństwo | argon2, Flask-Limiter, CSRF (Flask-WTF), zasady niżej | Lab 9 |
| Mapa | **Leaflet** + OpenStreetMap | — |
| Baza | **SQLite** (preinstalowane na AGH lab; Lab 9 demo też używa SQLite) | Lab 9 |
| Pliki | Supabase Storage lub Cloudinary (HTTPS outbound), fallback: lokalny katalog na AGH lab | — |
| Hosting | **AGH lab** (`*.lab.kis.agh.edu.pl`, „Proxy to standalone app server") | Lab 1 |

## Architektura wysokopoziomowa

**Jeden deployment — Flask serwuje wszystko**: szablony Jinja2, statyki, REST API, WebSocket. Frontend
i backend są w tym samym originie, więc cookie sesji jest first-party bez żadnej gimnastyki z CORS-em.

```
Przeglądarka ──HTTPS──▶ Reverse-proxy uczelni ──/static──▶ public_html/ (assety)
                                              ──unix socket──▶ Flask + Flask-SocketIO
                                                                  │
                                                                  ├──▶ SQLite (plik /home/<login>/data/tindog.db)
                                                                  └──▶ Storage plików (Supabase/Cloudinary lub lokalnie ~/uploads/)
```

- **Hosting AGH lab** (konfiguracja „Proxy to standalone app server"): proces aplikacji (`gunicorn`
  z workerem `gevent`) słucha na unix socket `/home/<login>/app.sock`; reverse-proxy uczelni forwardyje
  ruch z `https://<login>.lab.kis.agh.edu.pl/`. Pliki statyczne (CSS/JS/obrazy) lądują w
  `/home/<login>/public_html/` i są serwowane bezpośrednio jako `/static/*` (nie przechodzą przez Flask).
- **Konwencja katalogów na koncie AGH:** projekt klonujemy do `~/tindog/`, własny venv w `~/tindog/.venv/`,
  baza w `~/data/tindog.db` (poza katalogiem repo, żeby `git pull` nie ruszał danych). Demo z Lab 9
  zostaje w `~/app/` jako referencja — tylko jeden gunicorn na raz może słuchać na `~/app.sock`.
- **WebSocket przez proxy uczelni:** Socket.IO próbuje upgrade do WS; jeśli proxy go nie przepuszcza,
  **automatycznie wraca do long-pollingu** — czat zadziała tak czy inaczej. Sprawdzić to wcześnie.
- **Uwierzytelnianie:** sesja Flask-Login w cookie `httpOnly`, `Secure`, `SameSite=Lax`. Front i back
  w jednym originie ⇒ żadnych problemów cross-site.
- **Rodowód** jest grafem: model `Animal` odwołuje się sam do siebie przez `sire_id` (ojciec) i `dam_id`
  (matka). Przeglądanie przodków i liczenie inbredu = trawersowanie tego grafu (patrz `docs/MODEL_DANYCH.md`).

## Docelowa struktura repo

```
app/
  __init__.py            create_app() — fabryka aplikacji Flask
  models/                modele SQLAlchemy
  schemas/               schematy Pydantic (walidacja wejścia)
  routes/                blueprinty: auth, farms, animals, pedigree, match, chat, api
  services/              logika domenowa (dopasowania, inbred, weryfikacja)
  sockets/               handlery Flask-SocketIO (czat, powiadomienia)
  templates/             szablony Jinja2 (Bootstrap + Alpine.js)
  static/                CSS, JS, ikony — kopiowane do public_html/ na deployu
migrations/              Alembic (Flask-Migrate)
tests/                   pytest
docs/                    dokumentacja (model danych, decyzje)
requirements.txt
wsgi.py                  punkt wejścia dla gunicorna (produkcja)
.env.example
```

## Komendy

```bash
# Lokalnie (w aktywnym venv)
pip install -r requirements.txt
flask db upgrade                       # zastosuj migracje
flask db migrate -m "opis"             # nowa migracja po zmianie modeli
flask run                              # dev server (REST + Socket.IO + szablony)
pytest                                 # testy
pytest tests/test_x.py::test_y         # pojedynczy test

# Produkcja na AGH lab (po SSH)
gunicorn -k gevent -w 1 --bind unix:/home/$USER/app.sock wsgi:app
# Statyki kopiujemy do public_html/:
rsync -a app/static/ /home/$USER/public_html/
```

## Konwencje kodu

- **Czytelność ponad spryt.** Kod ma być zrozumiały dla każdego z 4 członków zespołu — każdy może zostać
  przepytany z dowolnego fragmentu. Unikaj „magii" i nieoczywistych skrótów.
- **Identyfikatory po angielsku** (zmienne, funkcje, klasy, tabele, pola) — standard.
- **Komentarze po polsku tam, gdzie wyjaśniają „dlaczego"** lub nieoczywistą logikę domenową (np. wzór na
  inbred, reguły dopasowania). Nie komentuj rzeczy oczywistych z kodu.
- Backend: **route → walidacja Pydantic → logika (serwis) → ORM**. Trzymaj logikę domenową poza handlerami
  tras, żeby dało się ją testować i ponownie używać.
- **Wygląd:** Bootstrap 5 z własną paletą i typografią w `app/static/css/` — unikamy „defaultowego BS"
  (typowe gradienty primary itp.). Komponenty oparte na tabelach, kartach, formularzach — zero swipe'ów
  i UX-u randkowego.
- **JS:** Alpine.js dla lokalnej reaktywności (modale, dropdowny, filtry), `fetch` dla AJAX-a, Socket.IO
  client dla zdarzeń live. **Nie** wciągamy frameworków typu React/Vue ani build pipeline'u — to poza
  zakresem labów.
- **API:** wszystkie endpointy JSON pod `/api/*`, udokumentowane Swaggerem (`/api/docs` lub
  `/apidocs`), zgodnie z Lab 6.

## Twarde reguły bezpieczeństwa i walidacji (priorytet oceny — Lab 9)

Prowadzący ocenia w szczególności **walidację danych wejściowych** i bezpieczeństwo. Bezwzględnie:

1. **Każdy** endpoint waliduje wejście schematem (Pydantic) zanim cokolwiek trafi do logiki/bazy.
   Nigdy nie ufaj danym z klienta.
2. **Tylko ORM (SQLAlchemy)**, zero sklejanego ręcznie SQL — chroni przed SQL injection.
3. **Autoryzacja właściciela:** użytkownik modyfikuje wyłącznie własne zasoby (np. `farm.owner_id ==
   current_user.id`). Sprawdzaj to przy KAŻDEJ operacji zapisu/edycji/usuwania, nie tylko w UI.
4. **Hasła** hashowane argon2; nigdy nie logowane ani nie zwracane w API.
5. **Upload plików:** waliduj typ MIME i rozmiar (zdjęcia, PDF rodowodów); nie ufaj rozszerzeniu z nazwy.
6. **Rate limiting** (Flask-Limiter) na logowaniu i rejestracji.
7. **CSRF:** tokeny CSRF na formularzach POST (Flask-WTF). Jeden origin nie zwalnia z tego.
8. **XSS:** Jinja2 escape'uje domyślnie — nie używaj `|safe` na danych z bazy / od użytkownika.
9. Cookie sesji `httpOnly` + `Secure` + `SameSite=Lax`. `SECRET_KEY` długi i z `.env`.
10. Nie zwracaj w API danych wrażliwych ani pól, których frontend nie potrzebuje.

### Mapowanie na moduły z Lab 9 (referencja: `~/app/modules/` na koncie AGH)

Każde z tych zagrożeń ma w aplikacji **świadomą przeciwwagę** — komentujemy ją w kodzie, żeby
prowadzący zobaczył, że nie tylko nas to ominęło, ale wiemy „dlaczego" i „gdzie":

| Lab 9 — moduł | Demo pokazuje | U nas |
|---|---|---|
| `sql.py` | f-string w zapytaniu → injection | wyłącznie SQLAlchemy ORM (parametryzacja); zero raw SQL |
| `xss.py` | reflektowanie inputu jako HTML | Jinja2 z domyślnym auto-escape; **nigdy `|safe`** na danych użytkownika |
| `csrf.py` | brak tokena → przejęcie sesji | Flask-WTF (token w sesji + walidacja); każdy POST ma token |
| `lfi.py` | user-controlled path do `open()` | uploady i serwowanie plików zawsze przez **whitelist** typów MIME i ścieżek |

## Reguły domenowe

- **Inbred:** przed zasugerowaniem pary licz pokrewieństwo kandydatów (oczekiwany współczynnik inbredu
  potomstwa) z grafu rodowodu i ostrzegaj/odfiltrowuj zbyt spokrewnione zwierzęta. Wzór i podejście:
  `docs/MODEL_DANYCH.md`.
- **Dopasowania** to algorytm (gatunek, rasa, płeć przeciwna, dostępność do rozrodu, bliskość na mapie,
  niski inbred) — nie osobny workflow akceptacji (nie jest w zakresie).
- **Mapa/odległość:** filtruj po promieniu na podstawie `latitude`/`longitude` hodowli.

## Czego nie robić

- Nie nadawać aplikacji estetyki/UX aplikacji randkowej (swipe'y itp.) — to narzędzie dla hodowców.
- **Nie wciągać frameworków frontendowych poza labami** (React, Vue, Svelte, build pipeline Vite/Webpack).
  Trzymamy się Jinja2 + Bootstrap + Alpine.js + Fetch.
- Nie dodawać funkcji spoza ustalonego zakresu bez uzgodnienia (ocena = realizacja ustalonych punktów).
- Nie obchodzić walidacji ani sprawdzania właściciela „na szybko" — to wprost obniża ocenę.
