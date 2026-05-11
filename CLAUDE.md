# Hantavirus Global Threat Monitor

Dashboard standalone HTML/JS che monitora l'outbreak di Hantavirus 2026 sulla
MV Hondius (outbreak **reale**, in corso da aprile 2026 — verificare WHO DON599,
ECDC, ISS, CDC per ogni aggiornamento).

## Regole di lavoro

- **Lingua**: rispondi sempre in italiano a Simone
- **Stile codice**: single-file HTML/JS, zero framework, zero CDN. D3.js e
  TopoJSON sono **bundled inline** nel file. Non aggiungere mai dipendenze
  esterne caricate da CDN.
- **Step-by-step**: per ogni modifica strutturale, mostra il piano e chiedi
  conferma prima di procedere. Niente refactor massivi senza approvazione.
- **Commit**: messaggi concisi in italiano, prefisso tipo `feat:`, `fix:`,
  `chore:`, `docs:`.
- **Workflow branch/PR**: lavora su branch dedicato (es. quello assegnato dal
  task), e per ogni pacchetto di modifiche sostanziali apri una PR verso `main`.
  Simone fa il merge manuale e poi assegna il branch successivo. Non pushare
  mai direttamente su `main`.
- **Test fisici**: dopo ogni modifica al rendering, ricorda a Simone di
  ricaricare la pagina su mobile (Chrome Android via GitHub Pages) per testare.
  Il file è stato debuggato a lungo per strict-mode mobile.

## Struttura file

```
index.html                # Dashboard standalone (~325 KB, ~2400 righe)
                          # D3 + TopoJSON bundled, niente import esterni
                          # Servita da GitHub Pages (rename da hantavirus_monitor.html)
.nojekyll                 # Disattiva processing Jekyll su GitHub Pages
.github/workflows/        # GitHub Actions (da creare)
data.json                 # Stato corrente (da creare, generato da workflow)
BRIEFING.md               # Contesto completo del progetto e decisioni prese
NEWS_UPDATE_2026-05-11.md # Aggiornamenti reali post-creazione dashboard
```

## Variabili globali (JS) — non rinominarle, sono cablate nel codice

| Variabile | Tipo | Mutabile | Note |
|-----------|------|----------|------|
| `COUNTRIES` | object (ISO numeric → {name,color,note}) | sì | 28 paesi base |
| `INCIDENTS` | array di marker | sì | 21 entry iniziali |
| `ROUTE` | array `[lon,lat]` | sì | 6 punti, finisce a Tenerife |
| `EVACUATIONS` | array `{coords,label,color}` | sì | 2 evacuazioni mediche |
| `FLIGHTS` | array `{coords,label,color}` | sì | 6 voli dispersione |
| `BASE_*_LEN` / `BASE_COUNTRY_KEYS` | snapshot | no | Servono per cache diff |
| `DATA` | object stat counters | sì | cases, deaths, monitored, cfr |
| `BASE_EVENTS` | array timeline | no | 24 eventi storici fissi |
| `dynamicEvents` | array | sì | Nuovi eventi da API |
| `_zoom _svg _proj _mapG _cfeat _pfn _currentDefcon _touchMode` | refs D3 | sì | **Dichiarati con `let` — non assegnare senza dichiarare, mobile Chrome è strict** |

## Funzioni chiave

- `applyData(data)` — anima i 4 stat counter
- `setDefcon(level)` — cambia barra DEFCON + glow
- `drawShipRoute()` / `drawEvacuations()` / `drawFlights()` — disegnano gli
  overlay rispettivi sulla mappa (chiamate da `initMap` e `refreshMapOverlays`)
- `refreshMapOverlays()` — ridisegna tutto senza ricreare la SVG (usata dopo
  aggiornamenti dinamici)
- `fetchUpdate()` — chiama Claude API. **Da rimuovere/sostituire** nel piano
  migrazione GitHub Pages (vedi BRIEFING.md)
- `maybeUpdate()` — restore stato dinamico da cache localStorage

## Schema JSON di aggiornamento atteso

Il sistema sa già processare questo schema (in `fetchUpdate`, righe ~1380-1620).
Quando migri a GitHub Actions, il workflow deve generare lo stesso schema in
`data.json`:

```json
{
  "ts": "ISO datetime",
  "cases": 9, "deaths": 3, "monitored": 147, "cfr": 33.3,
  "ship": "Tenerife (arrivo confermato 10 mag 2026)",
  "defcon": 4,
  "country_updates": [{"iso": "724", "color": "#ef4444", "note": "..."}],
  "new_countries":   [{"iso": "...", "name_it": "...", "color": "...", "note": "...", "lon": 0, "lat": 0, "marker_label": "..."}],
  "route_updates":   [{"lon": 0, "lat": 0, "label": "..."}],
  "new_evacuations": [{"from": [lon,lat], "to": [lon,lat], "label": "..."}],
  "new_flights":     [{"from": [lon,lat], "to": [lon,lat], "label": "..."}],
  "events":          [{"date": "DD mes YYYY", "text": "...", "type": "c|w|m", "tag": "..."}]
}
```

Colori validi: `#ef4444` (rosso/confermato), `#f59e0b` (ambra/sospetto),
`#22d3ee` (ciano/sorveglianza).

## Bug history (cose già risolte — NON reintrodurre)

- **Strict mode mobile Chrome**: tutte le variabili `_*` e le costanti
  `EVACUATIONS`/`FLIGHTS` **devono** essere dichiarate con `let`/`const`.
  Mai assegnare senza dichiarazione.
- **ROUTE finisce a Tenerife**, non a `[4.5, 52.3]` (Paesi Bassi). La nave
  è una rotta fisica; le rotte dei rimpatri sono in `FLIGHTS`.
- **Tre tipi di connessioni distinti** sulla mappa, mai unificarli:
  - ROUTE: ambra tratteggiata spessa (percorso nave)
  - EVACUATIONS: rosso tratteggiato fino con freccia (medical evac)
  - FLIGHTS: ciano ultra-sottile con freccia (rimpatri/dispersione)

## Fonti ufficiali consentite (citare solo queste)

WHO DON, ECDC, ISS+EpiCentro, Min. Salute IT, CDC, PAHO, RIVM (NL), RKI (DE),
UKHSA (UK), SPF (FR), UFSP (CH), Min. Sanidad ES, Min. Salud AR.
