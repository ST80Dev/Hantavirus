---
description: Aggiornamento manuale mirato di data.json — fetch fonti ufficiali via WebFetch, propone diff, chiede conferma prima del commit
allowed-tools: Read, Edit, Write, WebFetch, WebSearch, Bash, AskUserQuestion
---

# /aggiorna-hanta

Aggiornamento ragionato di `data.json` sull'outbreak Hantavirus 2026 (MV Hondius).
Sostituisce **per questo run** il workflow Actions automatico (cron 6h + Ollama),
leggendo direttamente le fonti ufficiali HTML, non solo RSS.

## Argomento opzionale

`$ARGUMENTS` può contenere un focus testuale (es. "Spagna", "voli rimpatrio",
"WHO DON di oggi"). Se vuoto, scansione completa di tutte le fonti `trusted`.

## Workflow obbligatorio

Esegui i passi in ordine. Non saltarne nessuno. Riporta a Simone alla fine
un riassunto in italiano dei cambiamenti proposti.

### 1. Stato di partenza

- Leggi `data.json` → memorizza `prev_data` (cases, deaths, monitored, cfr,
  ship, defcon, country_updates, events, ecc.)
- Leggi `sources.json` → carica `trusted`, `candidates`, `domain_whitelist`
- Leggi `CLAUDE.md` per ricordare schema JSON e colori validi
- Esegui `git status` e `git log -1 --format='%h %s'` per sapere da dove parti

### 2. Fetch fonti trusted (official + news)

Per ogni fonte in `sources.json:trusted` (ufficiali) e
`sources.json:news_trusted` (testate giornalistiche):

- **Tentativo primario**: `WebFetch url=<fonte.url> prompt="Estrai
  informazioni delle ultime 72h sull'outbreak Hantavirus MV Hondius 2026:
  casi cumulativi totali, decessi cumulativi, persone in sorveglianza,
  paesi coinvolti, evacuazioni mediche, voli rimpatrio, posizione nave.
  Riporta date e numeri esatti. Se la pagina non parla di Hantavirus,
  dillo esplicitamente."`
- **Fallback WebSearch (storicamente necessario)**: i domini governativi
  (who.int, ecdc.europa.eu, cdc.gov, gov.uk, paho.org, rivm.nl, rki.de,
  ecc.) restituiscono HTTP 403 a WebFetch dal sandbox Claude Code. Usa
  in alternativa:
  ```
  WebSearch query="hantavirus MV Hondius <focus o data> cases deaths"
           allowed_domains=[<lista da domain_whitelist_official>]
  ```
  e poi una seconda WebSearch più ampia su `domain_whitelist_news` per
  i dettagli locali. WebSearch funziona affidabilmente e restituisce
  sintesi datate dalle stesse fonti indicizzate da motori esterni.
- Salva il sunto della fonte in un buffer locale (mentale, non scrivere file)
- Se la fonte cita o linka un'**altra fonte** (PDF ufficiale, bollettino,
  articolo specifico) con dati nuovi, aggiungi quell'URL a una lista
  `to_explore`

Se l'argomento `$ARGUMENTS` è presente, dai priorità alle fonti che hanno
più probabilità di riguardarlo (es. focus "Spagna" → sanidad-es, who-don,
ecdc-threats, elpais, elmundo, abc.es prima).

### 2b. Distinzione official vs news

Le **official** (campo `trusted`) sono autoritative su numeri cumulativi
(cases, deaths, monitored) e sul defcon. Le **news** (`news_trusted`)
sono utili per:
- timeline degli eventi e dettagli geografici (chi è dove, quale ospedale)
- arrivare ai numeri quando le official sono in ritardo
- citazioni di funzionari (\"Schillaci: nessun pericolo\", \"Min. Butler\")

Per modificare `cases`/`deaths` cumulativi serve **almeno 1 fonte
official** che li confermi. Le news da sole non bastano per i contatori.
Per gli `events` e i `country_updates` (note testuali) le news bastano.

### 3. Esplorazione fonti scoperte

Per ogni URL nuovo in `to_explore`:

- Estrai il dominio.
- Se è in `domain_whitelist_official` → procedi con WebFetch/WebSearch,
  considera la fonte autoritativa per i numeri.
- Se è in `domain_whitelist_news` → procedi, ma usa la fonte solo per
  arricchire timeline/note testuali (non per `cases`/`deaths`).
- Se NON è in nessuna whitelist → ignora (rumore) **a meno che** più
  fonti trusted indipendenti citino lo stesso URL: in quel caso segnalalo
  a Simone e chiedi (`AskUserQuestion`) se promuoverlo a candidate.
- Per le fonti effettivamente utili, aggiungi voce in
  `sources.json:candidates` con campi: `id`, `name`, `url`, `lang`,
  `tier` (\"official\" o \"news\"), `notes` (\"scoperta il YYYY-MM-DD via
  <fonte_referente>\"), `discovered_at` (data ISO), `seen_count: 1`.
- Se una candidate compare in 3 run successive (controlla `seen_count`),
  proponi a Simone di promuoverla a `trusted`/`news_trusted`.

### 4. Sintesi e diff

Costruisci `new_data` partendo da `prev_data`, applicando solo le modifiche
giustificate da almeno una fonte ufficiale citata nel buffer:

**Regole hard (non negoziabili):**
- `cases` e `deaths` sono **cumulativi e monotoni crescenti**. Mai
  diminuirli, anche se una fonte parla di "casi attivi" o "guariti".
  Aumenta solo se una fonte cita un totale strettamente maggiore.
- `cfr` ricalcolato automaticamente come `round(deaths/cases*100, 1)`,
  mai inventato.
- `monitored` può scendere (dimessi/usciti da sorveglianza) o salire.
- Colori validi (vedi CLAUDE.md): `#ef4444` (confermato), `#f59e0b`
  (sospetto/allerta), `#22d3ee` (sorveglianza).
- `defcon` ∈ {1..5}; modificalo solo se la situazione è cambiata di
  livello.
- `events`: max 8 nuovi eventi più rilevanti dell'ultima settimana,
  in italiano, type ∈ {c, w, m, d}, con `tag` corto (es. "WHO DON5",
  "CDC HAN", "ECDC CDTR").
- Per `new_countries`: solo paesi mai apparsi prima in
  `country_updates` o `new_countries` dello stato precedente; richiede
  `iso` (ISO 3166-1 numerico string), `name_it`, `color`, `note`,
  `lon`, `lat`, `marker_label`.
- Cita per ogni numero modificato la fonte ufficiale precisa (URL +
  data) nel riassunto a Simone, non nel JSON.

### 5. Validazione

- Salva `new_data` su `data.json` (`Write` o `Edit`)
- Esegui `python scripts/validate_data.py data.json`
- Se fallisce: NON committare, mostra l'errore a Simone, chiedi cosa
  correggere
- Aggiorna `ts` con timestamp ms corrente solo se almeno un campo
  diverso da `ts` è cambiato

### 6. Salva sources.json

Se hai modificato `sources.json` (nuove candidates o `seen_count`
incrementati), scrivi anche quel file con `Write`.

### 7. Riepilogo + conferma

Mostra a Simone:

- Diff numerico: `cases X→Y, deaths X→Y, monitored X→Y, cfr X→Y`
- Nuovi country_updates / new_countries / new_evacuations / new_flights
  con la fonte di ciascuno
- Nuovi events (data + testo + tag fonte)
- Candidates aggiunte/promosse in `sources.json`
- Fonti consultate dove **non** hai trovato novità

Poi usa `AskUserQuestion` per chiedere: "Procedo con commit + push su
branch dedicato e apertura PR?" con opzioni "Sì, committa" / "Modifica
prima X" / "Annulla". **Non committare senza conferma.**

### 8. Commit + PR (solo se confermato)

- Crea branch nuovo: `git checkout -b claude/aggiorna-hanta-YYYY-MM-DD-HHMM`
- Commit (italiano, prefisso `chore:` o `feat:` se cambia stato significativo)
- Push: `git push -u origin <branch>`
- Apri PR verso `main` con MCP GitHub, descrizione che lista per ogni
  modifica la fonte ufficiale di riferimento

## Note operative

- **Mai** introdurre numeri non citati esplicitamente da una fonte
  whitelist; in caso di dubbio, lascia invariato e segnala a Simone.
- **Mai** rinominare le variabili globali JS in `index.html`
  (`COUNTRIES`, `INCIDENTS`, `ROUTE`, `EVACUATIONS`, `FLIGHTS`,
  `DATA`, `_zoom`, `_svg`, ecc. — vedi CLAUDE.md).
- Lingua: rispondi sempre in italiano nel riepilogo a Simone.
- Se WebFetch è bloccato per dominio non whitelistato, segnala
  `blocked` in `sources.json` (in `blocked`) con motivo + data, così
  i run successivi non riprovano.
