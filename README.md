# Hodowla — aplikacja webowa dla hodowców zwierząt

Projekt zaliczeniowy WWW (AGH SEM4). Zespół 4-osobowy.

Pełna dokumentacja:

- [`ONBOARDING.md`](ONBOARDING.md) — co budujemy, jak postawić projekt lokalnie, podział pracy.
- [`CLAUDE.md`](CLAUDE.md) — reguły kodu i bezpieczeństwa, mapowanie na laby kursu.
- [`docs/MODEL_DANYCH.md`](docs/MODEL_DANYCH.md) — encje, rodowód jako graf, algorytm dopasowań i inbredu.

## Szybki start (lokalnie)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pre-commit install
cp .env.example .env       # uzupełnij SECRET_KEY
python wsgi.py             # http://localhost:5001
```

Strona główna pokaże trzy diody — Flask, SQLite i Socket.IO. Wszystkie zielone = cały pociskiem
smugowy przeszedł.
