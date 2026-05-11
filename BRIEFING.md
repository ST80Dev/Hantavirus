# Briefing progetto — Migrazione a GitHub Pages + Actions

> Questo documento contiene il contesto completo della chat su Claude.ai
> dove la dashboard è stata sviluppata, e il piano di migrazione concordato
> con Simone. Leggilo prima di proporre cambiamenti strutturali.

## TL;DR

La dashboard è **funzionante** come file HTML standalone scaricato, MA il
sistema di auto-aggiornamento via Anthropic API direttamente dal browser
**non funziona** quando il file è servito da `file://` o `content://` (Chrome
mobile Android) a causa di CORS: `Access to fetch at 'https://api.anthropic.com'
from origin 'null' has been blocked by CORS policy`.

Soluzione concordata: **portare il progetto su GitHub Pages e generare
`data.json` lato server via GitHub Actions**, eliminando le chiamate API
dal browser.

## Contesto e cronologia

1. La dashboard è stata progettata per girare come artefatto Claude (dove
   le API venivano gestite dall'iframe Claude.ai automaticamente)
2. Scaricata come file standalone sul telefono Android di Simone, l'auto-update
   non funzionava più (CORS + niente proxy)
3. Sono state valutate 5 opzioni:

| # | Approccio | €/mese | Setup |
|---|-----------|--------|-------|
| 1 | Bottone "Aggiorna via Claude.ai" + copia-incolla manuale | 0 | 30 min |
| 2 | API key Anthropic personale incollata in pannello settings | ~6 | 10 min |
| 3 | Proxy Python su VPS OVH + Ollama Free + scraping RSS | 0 | 4-6 h |
| **5a** | **GitHub Pages + Actions + Anthropic API** | **~6** | **1-2 h** |
| **5b** | **GitHub Pages + Actions + Ollama Free + RSS reali** | **0** | **2-3 h** |

Simone ha **scelto la strada GitHub** (opzioni 5a o 5b). Da decidere con lui
quale variante adottare — la differenza è solo nel workflow che genera il
JSON, il resto della migrazione è identico.

## Piano di migrazione (steps in ordine)

### Step 1 — Setup base GitHub Pages
- Spostare `hantavirus_monitor.html` come `index.html` nel root del repo
  (o tenere nome originale e usare `index.html` come redirect — preferenza
  di Simone)
- Abilitare GitHub Pages nelle settings del repo, branch `main`, folder `/`
- Verificare che il sito sia accessibile e che la mappa si renderizzi
- Aspetta conferma da Simone via mobile prima di proseguire

### Step 2 — Refactor `fetchUpdate` per leggere `data.json` locale
- Rimuovere la chiamata `fetch('https://api.anthropic.com/v1/messages', ...)`
- Sostituire con `fetch('./data.json?t=' + Date.now())` (cache-bust)
- Mantenere lo stesso schema di parsing già implementato (righe ~1380-1620
  del file originale processano già tutti i campi)
- Stato di errore se `data.json` non esiste: mostrare banner "modalità statica"
- Aggiornare `maybeUpdate()`: se `data.json` è più recente del localStorage
  cache, riapplicarlo; altrimenti usa cache
- Commit con `data.json` placeholder iniziale che riproduca lo stato corrente

### Step 3 — Decidere: 5a (Anthropic) o 5b (Ollama)

**Chiedere a Simone:** preferisce €6/mese per la qualità Claude+web_search
(opzione 5a), oppure zero costi accettando un workflow un po' più articolato
con Ollama + scraping RSS (opzione 5b)?

### Step 4a — Workflow GitHub Actions (variante Anthropic)
File `.github/workflows/update-data.yml`:
- Schedulato ogni 4 ore + manuale (`workflow_dispatch`)
- Setup Node.js o Python
- Step che chiama `api.anthropic.com/v1/messages` con:
  - Modello: `claude-opus-4-7` (o il modello scelto al momento del deploy
    — verificare disponibilità su docs.claude.com)
  - Tool: `web_search_20250305` abilitato
  - System prompt: vedi prompt in `fetchUpdate` originale (righe ~1310-1360
    del file). Lo schema JSON di output è già definito lì
  - Header: `x-api-key` da `${{ secrets.ANTHROPIC_API_KEY }}`
- Step che committa `data.json` aggiornato (con `git config` e auto-push)
- Tag/release opzionale per archivio storico

### Step 4b — Workflow GitHub Actions (variante Ollama + RSS)
File `.github/workflows/update-data.yml`:
- Schedulato ogni 4 ore
- Step 1 — fetch RSS feeds di fonti ufficiali:
  - WHO DON: `https://www.who.int/feeds/entity/csr/don/en/rss.xml`
  - ECDC threats: `https://www.ecdc.europa.eu/en/threats-and-outbreaks/rss.xml`
  - ISS EpiCentro: vedi `https://www.epicentro.iss.it/rss/`
  - Min. Salute IT: `https://www.salute.gov.it/portale/news/p3_2_1.jsp?lingua=italiano`
  - (verificare URL aggiornati al momento del setup)
- Step 2 — passare il testo aggregato a Ollama Cloud:
  - Endpoint: `https://ollama.com/v1/chat/completions` (OpenAI compatible)
  - Header `Authorization: Bearer ${{ secrets.OLLAMA_API_KEY }}`
  - Modello consigliato: `gpt-oss:120b-cloud` (buon compromesso struttura/qualità)
  - Prompt: estrae lo schema JSON definito in CLAUDE.md → output
- Step 3 — validare il JSON (chiave per chiave) prima di committarlo
- Step 4 — committa `data.json`

### Step 5 — Hardening
- Validazione schema JSON prima del commit (un workflow rotto non deve
  rompere la dashboard)
- Fallback: se il workflow fallisce, `data.json` resta com'era → dashboard
  continua a mostrare l'ultimo stato valido
- Logging: ogni run del workflow scrive un commit con messaggio tipo
  `chore: data update YYYY-MM-DD HH:mm — X nuovi eventi`
- Opzionale: file `history/data-YYYY-MM-DD-HH.json` per archivio storico

### Step 6 — UI cleanup
- Rimuovere il countdown "Prossimo aggiornamento tra Xh Xm" o ricalcolarlo
  basato su `last-modified` di `data.json`
- Mostrare timestamp dell'ultimo aggiornamento reale (dal JSON, non dal client)
- Pulire localStorage cache logic — ora il source-of-truth è il file remoto
- Aggiungere link al repo nel footer per trasparenza

## Vincoli e preferenze Simone

- **Italiano** sempre nelle interazioni e nei commenti
- **Single-file HTML** per la dashboard, niente refactor in multi-file SPA
- **Conferma step-by-step** prima di modifiche strutturali
- **No frameworks nuovi**, no aggiunte di dipendenze CDN
- **Mobile-first testing**: ogni cambio va validato su Chrome Android
- Familiarità con Claude Code workflow + commit diretti su `main`
- Ha già VPS OVH con Docker (se servisse fallback proxy)
- Ha piano Claude Max (non utile per API, ma utile per claude.ai manuale)
- Ha Ollama Free Cloud (chiave API disponibile)
- Vive a Tavullia (Italia), fuso CEST/CET — utile per pianificare schedule
  workflow (suggerisco run alle 06:00, 12:00, 18:00, 00:00 CET)

## Cose già risolte (NON reintrodurre)

Vedi `CLAUDE.md` sezione "Bug history".

## Dati che potrebbero essere stantii (al 11 mag 2026)

La dashboard al momento riflette lo stato dell'outbreak al **~10 mag 2026**.
Tra l'ultima generazione e oggi, ci sono notizie nuove che è bene
incorporare manualmente nel `data.json` iniziale prima di lasciare partire
il workflow. Vedi `NEWS_UPDATE_2026-05-11.md` per i dettagli.
