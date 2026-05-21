# Model danych

Opisowy schemat bazy (PostgreSQL / SQLAlchemy). To punkt wyjścia — pola dopracowujemy wspólnie przed
implementacją. Każda encja ma `id` (PK) i `created_at`; pomijam je niżej dla zwięzłości.

## Diagram relacji (skrót)

```
User 1───* Farm 1───* Animal ──┐ sire_id ─┐ (self-reference: rodowód)
                       │        └ dam_id ──┘
                       │
                       *───* Document (typ: rodowód / książeczka / certyfikat)

User *───* Conversation ───* Message
User 1───* Notification
User 1───* Favorite ──▶ (Animal lub Farm)
```

## Encje

### User — konto (hodowca / admin)
- `email` — unikalny, walidowany formatem
- `password_hash` — argon2 (nigdy w odpowiedzi API)
- `display_name`
- `role` — `user` | `admin` (admin do moderacji / weryfikacji)
- Relacje: `farms` (1:N)

### Farm — hodowla (publiczny profil)
- `owner_id` → User
- `name`, `description`
- `species` — główny gatunek hodowli (`dog` | `horse` | `cat` | …)
- `address` (tekst), `latitude`, `longitude` — do wyszukiwania po mapie i filtrowania po promieniu
- `is_verified` — odznaka „zweryfikowany hodowca"
- `avatar_url`, zdjęcia
- Relacje: `animals` (1:N)
- **Autoryzacja:** edytuje wyłącznie `owner`.

### Animal — zwierzę (rdzeń aplikacji)
- `farm_id` → Farm
- `name`, `species`, `breed`, `sex` (`male` | `female`), `birth_date`, `color`
- `registration_number` — numer rodowodowy
- `available_for_breeding` (bool) — czy dostępne do rozrodu
- `description`, zdjęcia
- **`sire_id` → Animal (nullable)** — ojciec
- **`dam_id` → Animal (nullable)** — matka
- Self-reference `sire_id`/`dam_id` tworzy **graf rodowodu**: przeglądanie przodków = rekurencyjne
  schodzenie po tych dwóch polach.

### Document — dokumenty (weryfikacja rodowodu, książeczki)
- `animal_id` → Animal (lub `farm_id`)
- `type` — `pedigree` | `health_booklet` | `certificate`
- `file_url` — plik w Storage (Supabase/Cloudinary), nie w bazie
- `is_verified` — flaga weryfikacji (np. przez admina)
- **Walidacja przy uploadzie:** typ MIME i rozmiar (PDF/zdjęcia), nie ufamy rozszerzeniu z nazwy.

### Conversation + Message — czat (WebSocket)
- **Conversation:** uczestnicy (M:N do User; dla 1:1 mogą wystarczyć `user_a_id` / `user_b_id`)
- **Message:** `conversation_id` → Conversation, `sender_id` → User, `body`, `sent_at`, `read_at` (nullable)
- Wiadomości lecą przez Flask-SocketIO w czasie rzeczywistym **i** są zapisywane do bazy (historia).

### Favorite — ulubione
- `user_id` → User
- cel: `animal_id` (nullable) **lub** `farm_id` (nullable) — z `CHECK`, że dokładnie jedno jest ustawione
- unikalność na (user, cel), żeby nie dublować

### Notification — powiadomienia
- `recipient_id` → User
- `type` — np. `new_message` | `favorited_you` | `document_verified`
- `payload` (JSON) — dane kontekstowe (kto/co)
- `is_read` (bool)
- Tworzone wraz ze zdarzeniem i wypychane przez WebSocket; lista offline z bazy.

### (opcjonalnie) Breed — słownik ras
- Normalizacja `breed` do tabeli ułatwia filtrowanie i autouzupełnianie. Na start może być stringiem.

## Algorytm: dopasowania

Sugerowanie partnera dla danego zwierzęcia to **zapytanie/serwis**, nie osobny workflow akceptacji.
Kryteria (kandydaci spełniający warunki, posortowani):
1. ten sam `species`, zgodna `breed`,
2. **płeć przeciwna**, `available_for_breeding = true`,
3. bliskość geograficzna (promień od hodowli pytającego — `latitude`/`longitude`),
4. **niski współczynnik inbredu** potomstwa (patrz niżej) — zbyt spokrewnione odrzucamy/ostrzegamy.

## Algorytm: współczynnik inbredu

Inbred potomstwa pary (X, Y) = **współczynnik pokrewieństwa (kinship)** rodziców, liczony z grafu rodowodu
(`sire_id`/`dam_id`). Wzór Wrighta — suma po wspólnych przodkach `A`:

```
F = Σ_A (1/2)^(n1 + n2 + 1) · (1 + F_A)
```

gdzie `n1`, `n2` to długości ścieżek od X i od Y do wspólnego przodka `A`, a `F_A` to inbred samego `A`
(rekurencyjnie; często upraszczany do 0 przy braku danych).

Implementacja: zbierz przodków X i Y (z głębokością wpływa na trafność), znajdź wspólnych, zsumuj wkłady.
Używamy tego, by **ostrzegać/odfiltrowywać** zbyt spokrewnione pary w dopasowaniach. To dobry, nietrywialny
fragment „do obrony" — warto rozumieć każdy człon wzoru.
