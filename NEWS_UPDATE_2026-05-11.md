# Aggiornamenti reali outbreak — 11 mag 2026

Dati nuovi rispetto alla dashboard (che riflette lo stato al 10 mag 2026 circa).
**Verificare comunque con fonti ufficiali** prima di committarli — questa è
una sintesi da news search del 11 mag e potrebbe contenere imprecisioni.

## Casi totali

- **9 casi** confermati/probabili (era 8)
- 2-3 decessi confermati (le fonti variano; WHO DON599 ne conta 3, ABC News
  parla di "2 confirmed + 1 suspected")
- CFR ~25-33% (aggiustare in base ai numeri scelti)

## Eventi dell'10-11 mag 2026

- **10 mag, ~05:30 ora locale** — MV Hondius attracca a **Port of Granadilla,
  Tenerife** (Canarie). Fonti: Wikipedia, CNN, WHO
- **10 mag** — Inizia evacuazione coordinata. Ministra Salute spagnola
  Mónica García descrive l'operazione come "senza precedenti"
- **10 mag, sera** — **94 persone di 19 nazionalità** sbarcate il primo giorno
- **10 mag** — **17 cittadini USA + 1 britannico residente USA** evacuati su
  volo Department of State diretto a **Offutt AFB, Omaha, Nebraska** →
  University of Nebraska Medical Center (National Quarantine Unit)
- **10 mag** — Su quel volo, **1 passeggero americano risulta PCR positivo**;
  un secondo ha sintomi lievi. Trasportati in unità di biocontenimento
- **10 mag, notte (CEST)** — Volo di rimpatrio francese atterra a **Le Bourget**
  (Parigi). **Un passeggero mostra sintomi sul volo**; condizioni peggiorate
  durante la notte. Ricoverato in ospedale specializzato in malattie
  infettive. Ministra Catherine Rist annuncia **22 "contact cases"** francesi
  già identificati su 2 voli
- **11 mag** — Continuano le evacuazioni dalla nave (resta una giornata)

## Aggiornamenti specifici per dashboard

### Country updates necessari
- 🇫🇷 **Francia** (ISO 250): da `#22d3ee` (sorveglianza) → `#ef4444` (caso
  confermato) — passeggero sintomatico in ospedale Parigi + 22 contact cases
- 🇺🇸 **Stati Uniti** (ISO 840): da `#22d3ee` → `#ef4444` — 1 PCR+ confermato
  al Nebraska Biocontainment Unit

### New flights da aggiungere
- Tenerife → Omaha (Offutt AFB) — Volo Department of State USA, 18 passeggeri
- Tenerife → Le Bourget (Parigi) — Volo rimpatrio Francia (passeggero
  sintomatico a bordo)

### Eventi timeline da aggiungere
```
{date: "10 mag 2026", text: "⚓ MV Hondius attracca a Port of Granadilla (Tenerife) ore 05:30. Inizia evacuazione coordinata.", type: "m", tag: "ARRIVO"}
{date: "10 mag 2026", text: "🇺🇸 USA — 17 cittadini + 1 britannico evacuati a Offutt AFB (Nebraska). 1 PCR+ confermato in volo.", type: "c", tag: "EVAC USA"}
{date: "10 mag 2026", text: "🇫🇷 Francia — Volo rimpatrio Le Bourget. 1 passeggero sintomatico ricoverato. 22 contact cases identificati.", type: "c", tag: "EVAC FR"}
{date: "11 mag 2026", text: "🌐 Casi totali confermati/probabili: 9. Sbarchi MV Hondius proseguono.", type: "w", tag: "UPDATE"}
```

### Ship position update
`ship: "Tenerife – Port of Granadilla (sbarco in corso)"`

## Fonti consultate (citate in chat)

- Wikipedia: "MV Hondius hantavirus outbreak"
- WHO DON599: https://www.who.int/emergencies/disease-outbreak-news/item/2026-DON599
- CDC press release: https://www.cdc.gov/media/releases/2026/2026-cdc-provides-update-on-hantavirus-outbreak-linked-to-m-v-hondius-cruise-ship.html
- CNN live: https://www.cnn.com/2026/05/10/health/live-news/hantavirus-cruise-outbreak
- ABC News: https://abcnews.com/International/live-updates/hantavirus-live-updates-mv-hondius-canary-islands/
- PBS News
- Live Science

Quando crei `data.json` per la prima volta, fai una **fresh web search**
prima di committare — la situazione cambia di ora in ora.
