# Hodowla — aplikacja webowa dla hodowców zwierząt

Projekt zaliczeniowy WWW (AGH SEM4). Zespół 4-osobowy.

Profesjonalna platforma dla hodowców psów, koni i kotów: katalog hodowli, profile zwierząt z rodowodami,
mapa, czat w czasie rzeczywistym, algorytm dopasowań ze współczynnikiem inbredu, ulubione i powiadomienia.

**Dokumentacja:**
- [`ONBOARDING.md`](ONBOARDING.md) — co budujemy, podział pracy, deploy na AGH lab
- [`CLAUDE.md`](CLAUDE.md) — reguły kodu i bezpieczeństwa, mapowanie na laby kursu
- [`docs/MODEL_DANYCH.md`](docs/MODEL_DANYCH.md) — encje, graf rodowodu, algorytm inbredu

---

## Wymagania

- **Python 3.11+**
- **Git**
- (macOS) Narzędzia Xcode CLI — `gevent` kompiluje się ze źródeł

---

## Uruchomienie — macOS / Linux

```bash
# 1. Sklonuj i wejdź do katalogu
git clone https://github.com/AntttPe/www_projekt.git
cd www_projekt

# 2. Środowisko wirtualne
python3 -m venv .venv
source .venv/bin/activate

# 3. Zależności (runtime + dev: ruff, pytest, pre-commit)
pip install --upgrade pip
pip install -r requirements-dev.txt

# 4. Pre-commit hooki (formatowanie przed commitem)
pre-commit install

# 5. Plik konfiguracyjny — skopiuj szablon i wygeneruj SECRET_KEY
cp .env.example .env
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(64))"
# ↑ skopiuj wynik do .env zastępując pustą linię SECRET_KEY=

# 6. Baza danych (SQLite, plik tworzony automatycznie w instance/)
flask db upgrade            # jeśli migracje już są w repo
# albo, jeśli zaczynasz świeżo (brak migrations/):
# flask db init
# flask db migrate -m "init schema"
# flask db upgrade

# 7. Wgranie przykładowych danych
flask seed

# 8. Uruchomienie aplikacji
python wsgi.py
```

Otwórz **http://localhost:5001**.

> Port 5001 zamiast 5000 — na macOS od Monterey port 5000 jest zajęty przez AirPlay Receiver.

---

## Uruchomienie — Windows (PowerShell)

```powershell
# 1. Sklonuj i wejdź do katalogu
git clone https://github.com/AntttPe/www_projekt.git
cd www_projekt

# 2. Środowisko wirtualne
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
# Jeśli PowerShell blokuje skrypty, jednorazowo:
#   Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

# 3. Zależności
python -m pip install --upgrade pip
pip install -r requirements-dev.txt

# 4. Pre-commit hooki
pre-commit install

# 5. Plik konfiguracyjny
Copy-Item .env.example .env
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(64))"
# ↑ skopiuj wynik do .env zastępując pustą linię SECRET_KEY=

# 6. Baza danych
flask db upgrade
# albo, jeśli zaczynasz świeżo (brak migrations/):
# flask db init
# flask db migrate -m "init schema"
# flask db upgrade

# 7. Wgranie przykładowych danych
flask seed

# 8. Uruchomienie aplikacji
python wsgi.py
```

Otwórz **http://localhost:5001**.

> Na Windows AirPlay nie blokuje portu 5000, ale i tak używamy 5001 dla spójności w zespole.

---

## Konta demonstracyjne (po `flask seed`)

Hasło wszystkich kont: **`demo12345`**

| Email | Hodowca | Hodowla | Gatunek |
|---|---|---|---|
| `anna@hodowla.test` | Anna Kowalska | Stadnina Wschodni Wiatr | Konie arabskie |
| `marek@hodowla.test` | Marek Wiśniewski | Border Collies z Pszczyny | Psy |
| `kasia@hodowla.test` | Katarzyna Lis | Kennel Złoty Liść | Psy (Golden Retriever) |
| `piotr@hodowla.test` | Piotr Zając | Stadnina Mała Wieś | Konie półkrwi |
| `julia@hodowla.test` | Julia Nowak | Kocia Łapka — Maine Coon | Koty |
| `andrzej@hodowla.test` | Andrzej Dąbrowski | Hodowla Stado Białego Domu | Owczarki niemieckie |

Albo załóż swoje konto przez `/auth/register`.

---

## Najważniejsze ścieżki

| URL | Co tam jest |
|---|---|
| `/` | Landing z hero, statystykami, wyróżnionymi hodowlami |
| `/farms` | Katalog hodowli z filtrami (gatunek, województwo, weryfikacja), paginacja |
| `/farms/<id>` | Profil hodowli, mini-mapa, lista zwierząt, kontakt |
| `/animals` | Katalog zwierząt z filtrami (gatunek, płeć, rasa, dostępność do rozrodu) |
| `/animals/<id>` | Profil z rodowodem 2 pokoleń, ostrzeżeniem inbredu, akcjami właściciela |
| `/animals/<id>/matches` | Sugerowane pary do rozrodu (inbred + dystans) |
| `/map` | Mapa Leaflet z wszystkimi hodowlami |
| `/chat` | Czat realtime przez Socket.IO |
| `/dashboard` | Mój panel (po zalogowaniu) |
| `/notifications` | Lista powiadomień |
| `/api/docs` | Skrót endpointów REST API |

---

## API

Pełna lista pod `/api/docs`. Kluczowe:

```http
GET    /api/farms                          # lista (opcjonalnie ?species=)
GET    /api/farms/<id>                     # profil hodowli
POST   /api/farms                          # utwórz (auth)
PATCH  /api/farms/<id>                     # edycja (właściciel)

GET    /api/animals                        # lista (?species=&sex=&available=1)
GET    /api/animals/<id>/pedigree          # przodkowie do 4 pokoleń
GET    /api/animals/<id>/matches           # dopasowania z inbredem i dystansem

GET    /api/inbreeding?a=1&b=2             # współczynnik inbredu pary
```

Każdy POST/PATCH waliduje wejście schematem **Pydantic** i sprawdza autoryzację właściciela.

---

## Testy

```bash
pytest                          # cały zestaw
pytest tests/test_smoke.py -v   # smoke test (działa na in-memory SQLite)
```

---

## Najczęstsze potknięcia

| Objaw | Przyczyna | Rozwiązanie |
|---|---|---|
| `command not found: python` | macOS ma tylko `python3` | Użyj `python3 -m venv .venv`, po aktywacji venva `python` zadziała |
| `Permission denied: .venv/bin/activate` | Brakuje `source` | Użyj `source .venv/bin/activate` |
| `unable to open database file` | Brakuje katalogu `instance/` | `mkdir -p instance`, potem `flask db upgrade` |
| Biała strona na `http://localhost:5000` | macOS AirPlay zajmuje 5000 | Otwórz `http://localhost:5001` |
| `gevent` nie kompiluje się (macOS) | Brak Xcode CLI | `xcode-select --install`, potem `pip install -r requirements-dev.txt` |
| Pre-commit odrzuca commit | Ruff format / linter nie przeszedł | Uruchom `ruff format .` i `ruff check --fix .`, dodaj zmiany |
