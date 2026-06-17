# Zdjęcia stockowe (lokalne)

Tu wrzucasz **dobre** zdjęcia, które zastępują tymczasowe, tandetne obrazki z
loremflickr. Aplikacja bierze je automatycznie — nie trzeba zmieniać kodu.

## Foldery — jeden na gatunek

Nazwy folderów muszą się zgadzać z kluczami gatunków z modelu
(`app/models/farm.py` → `SPECIES_CHOICES`):

```
img/stock/dog/      ← psy
img/stock/cat/      ← koty
img/stock/horse/    ← konie
```

Plik trafia do galerii danego gatunku po prostu przez wrzucenie go do folderu.
Nazwa pliku jest dowolna (`pies-01.jpg`, `border-collie.webp`, cokolwiek).

## Format — żeby NIC się nie ucinało

W całej aplikacji kadr zdjęcia ma proporcje **3:2** (poziomo). Zdjęcie w innym
kształcie zostanie dopełnione przez `object-fit: cover`, czyli przycięte do
środka. Dlatego:

| Co | Wartość |
|---|---|
| **Proporcje** | **3:2 poziomo** (szerokość : wysokość) |
| **Zalecany rozmiar** | **1200 × 800 px** (albo większy w tej proporcji, np. 1500 × 1000) |
| Minimum | 900 × 600 px (niżej widać miękkość na większych ekranach) |
| Format pliku | `.jpg`, `.jpeg`, `.png` lub `.webp` (`.webp` = najlżejszy) |
| Waga pliku | trzymaj poniżej ~300–500 KB na zdjęcie (skompresuj) |

Najprościej: w dowolnym edytorze (Photopea, Canva, Preview na Macu) ustaw
kadr/eksport na **3:2** i wyeksportuj 1200×800.

## Ile zdjęć dodać

**6–8 na gatunek** w zupełności wystarczy. Wybór zdjęcia dla danej hodowli/
zwierzęcia jest **deterministyczny po `id`** (rekord nr 7 zawsze dostaje to samo
zdjęcie), więc przy kilkunastu rekordach 6–8 zdjęć daje przyjemną różnorodność
i nic się nie powtarza zbyt nachalnie. Mniej niż 3 → widać powtórki.

## Po dodaniu plików

- **Dev (`python wsgi.py` / `flask run`):** wystarczy odświeżyć stronę — lista
  jest przeliczana na bieżąco w trybie debug.
- **Produkcja:** lista jest cache'owana — zrestartuj proces gunicorna po
  wgraniu nowych zdjęć. Pamiętaj też o `rsync` statyków do `public_html/`
  (patrz CLAUDE.md → Komendy).

## Gdy folder jest pusty

Jeśli dla gatunku nie ma żadnego pliku, aplikacja używa loremflickr jako
fallbacku (a gdy i to padnie — eleganckiego medalionu z ikoną). Czyli brak
zdjęć niczego nie psuje.
