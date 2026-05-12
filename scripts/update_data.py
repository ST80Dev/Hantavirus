#!/usr/bin/env python3
"""Genera data.json aggregando RSS ufficiali e chiamando Ollama Cloud.

Flusso:
1. Legge data.json corrente come "stato precedente"
2. Fetcha RSS hantavirus-related da WHO/ECDC/ISS (lookback 14gg)
3. Costruisce prompt con stato precedente + RSS
4. Chiama Ollama Cloud (gpt-oss:120b-cloud) chiedendo JSON nello schema dashboard
5. Estrae JSON dalla risposta + merge difensivo con stato precedente
6. Scrive data.json (pretty-printed per diff git leggibili)

Lo script NON valida lo schema: quello è compito di validate_data.py, eseguito
come step successivo nel workflow. Se la validazione fallisce, il workflow
esce con errore e niente viene committato.
"""
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import feedparser
import requests

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data.json"

OLLAMA_URL = "https://ollama.com/v1/chat/completions"
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gpt-oss:120b-cloud")
OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY")

RSS_FEEDS = [
    ("WHO DON",         "https://www.who.int/feeds/entity/csr/don/en/rss.xml"),
    ("ECDC threats",    "https://www.ecdc.europa.eu/en/threats-and-outbreaks/rss.xml"),
    ("ISS EpiCentro",   "https://www.epicentro.iss.it/rss/rss.xml"),
    ("ISS news",        "https://www.iss.it/rss"),
    ("Min. Salute IT",  "https://www.salute.gov.it/portale/news/p3_2_1_1.jsp?menu=notizie&tipo=rss"),
]

KEYWORDS = re.compile(
    r"hantavirus|hantaviral|\bhanta\b|hondius|andes\s*virus|"
    r"\bdon\s*\d{2,4}\b|\bHPS\b|\bHFRS\b|sin\s*nombre|"
    r"pulmonary\s*syndrome|sindrome\s*polmonare|febbre\s*emorragica",
    re.I,
)
LOOKBACK_DAYS = 14
MAX_CONTEXT_CHARS = 8000
MAX_RAW_TITLES_LOG = 8


def log(msg):
    print(f"[update] {msg}", flush=True)


def fetch_rss_items():
    cutoff = datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)
    collected = []
    for name, url in RSS_FEEDS:
        try:
            parsed = feedparser.parse(
                url,
                request_headers={"User-Agent": "Hantavirus-Monitor/1.0 (+github.com/ST80Dev/Hantavirus)"},
            )
            entries = parsed.entries or []
            log(f"{name}: {len(entries)} entries totali")
            raw_titles_logged = 0
            in_window = 0
            for e in entries:
                title = (e.get("title") or "").strip()
                summary = (e.get("summary") or e.get("description") or "").strip()
                link = e.get("link") or ""
                published = None
                for k in ("published_parsed", "updated_parsed"):
                    if e.get(k):
                        published = datetime(*e[k][:6], tzinfo=timezone.utc)
                        break
                if published and published < cutoff:
                    continue
                in_window += 1
                if raw_titles_logged < MAX_RAW_TITLES_LOG:
                    date_str = published.date().isoformat() if published else "??"
                    log(f"  · [{name}] {date_str} — {title[:140]}")
                    raw_titles_logged += 1
                if not KEYWORDS.search(title + " " + summary):
                    continue
                clean_summary = re.sub(r"<[^>]+>", "", summary)
                clean_summary = re.sub(r"\s+", " ", clean_summary).strip()[:600]
                log(f"  ✓ MATCH [{name}] {title[:140]}")
                collected.append({
                    "source": name,
                    "title": title,
                    "summary": clean_summary,
                    "link": link,
                    "date": published.isoformat() if published else "",
                })
            log(f"  → {name}: {in_window} entries nella finestra {LOOKBACK_DAYS}gg")
        except Exception as ex:
            log(f"{name}: errore fetch ({ex.__class__.__name__}: {ex}) — salto")
    log(f"Entries hantavirus-related dopo filtro: {len(collected)}")
    return collected


def build_prompt(prev_data, rss_items):
    rss_blob = ""
    for it in rss_items:
        block = (
            f"\n## [{it['source']}] {it['date']} — {it['title']}\n"
            f"{it['summary']}\nFonte: {it['link']}\n"
        )
        if len(rss_blob) + len(block) > MAX_CONTEXT_CHARS:
            break
        rss_blob += block
    if not rss_blob:
        rss_blob = "(nessuna entry RSS rilevante negli ultimi 14 giorni)"

    system = (
        "Sei un sistema di intelligence epidemiologica. Aggiorni un dashboard "
        "sull'outbreak Hantavirus 2026 (MV Hondius, Andes virus).\n\n"
        "Ti vengono forniti:\n"
        "1. Lo STATO PRECEDENTE come JSON\n"
        "2. Una raccolta di entry RSS ufficiali (WHO, ECDC, ISS) degli ultimi 14 giorni\n\n"
        "Devi produrre il NUOVO data.json. Regole:\n"
        "- Mantieni TUTTI i campi dello stato precedente; modifica solo ciò che è cambiato realmente\n"
        "- cases/deaths/monitored: aggiorna SOLO se le fonti citano numeri nuovi\n"
        "- ship: aggiorna se la nave si è spostata\n"
        "- defcon: cambia solo se la situazione è cambiata di livello (1=pandemic, 5=normale)\n"
        "- country_updates: paesi GIÀ in lista con cambio di stato (iso ISO 3166-1 numerico come stringa)\n"
        "- new_countries: paesi mai apparsi prima (richiede iso, name_it, color, note, lon, lat)\n"
        "- new_flights / new_evacuations: solo se NUOVI rispetto allo stato precedente\n"
        "- events: max 8 eventi più rilevanti dell'ultima settimana, in italiano, type in {c,w,m,d}\n"
        "- Colori validi: #ef4444 (caso confermato/decesso), #f59e0b (sospetto/allerta), #22d3ee (sorveglianza)\n"
        "- NON inventare numeri o paesi: se le fonti non lo dicono, lascia invariato\n\n"
        "Rispondi SOLO con il JSON minificato. Niente markdown, niente testo prima o dopo."
    )

    user = (
        f"STATO PRECEDENTE:\n{json.dumps(prev_data, ensure_ascii=False)}\n\n"
        f"ENTRY RSS RECENTI:\n{rss_blob}\n\n"
        f"Data corrente: {datetime.now(timezone.utc).isoformat()}\n\n"
        "Produci il nuovo data.json."
    )

    return system, user


def call_ollama(system, user, max_retries=3):
    if not OLLAMA_API_KEY:
        raise RuntimeError("OLLAMA_API_KEY non configurata nell'environment")

    last_err = None
    for attempt in range(max_retries):
        wait = 5 * (2 ** attempt)  # 5, 10, 20s
        try:
            resp = requests.post(
                OLLAMA_URL,
                headers={
                    "Authorization": f"Bearer {OLLAMA_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": OLLAMA_MODEL,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": 0.2,
                },
                timeout=180,
            )
            if resp.status_code == 429 or 500 <= resp.status_code < 600:
                last_err = f"HTTP {resp.status_code}"
                log(f"Ollama {last_err} (tentativo {attempt + 1}/{max_retries}), retry in {wait}s")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            payload = resp.json()
            return payload["choices"][0]["message"]["content"]
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            last_err = f"{e.__class__.__name__}: {e}"
            log(f"Ollama network error: {last_err} (tentativo {attempt + 1}/{max_retries}), retry in {wait}s")
            time.sleep(wait)

    raise RuntimeError(f"Ollama failed dopo {max_retries} tentativi (ultimo errore: {last_err})")


def extract_json(text):
    cleaned = re.sub(r"```(?:json)?\s*", "", text).replace("```", "").strip()
    m = re.search(r"\{[\s\S]*\}", cleaned)
    if not m:
        raise ValueError("Nessun oggetto JSON trovato nella risposta Ollama")
    return json.loads(m.group(0))


def merge_with_prev(new_data, prev_data):
    """Fallback difensivo: se l'LLM omette un campo, recuperalo dallo stato precedente.

    NB: NON aggiorna `ts` qui — viene fatto solo in main() dopo aver verificato
    che esistono cambiamenti sostanziali rispetto allo stato precedente.
    """
    scalar_keys = ("cases", "deaths", "monitored", "cfr", "ship", "defcon")
    for k in scalar_keys:
        if k not in new_data and k in prev_data:
            new_data[k] = prev_data[k]
    for k in ("country_updates", "new_countries", "route_updates",
              "new_evacuations", "new_flights", "events"):
        if k not in new_data:
            new_data[k] = prev_data.get(k, [])
    return new_data


def has_substantive_changes(new_data, prev_data):
    """True se almeno un campo diverso da `ts` è cambiato fra new_data e prev_data."""
    keys = set(new_data.keys()) | set(prev_data.keys())
    keys.discard("ts")
    for k in keys:
        if new_data.get(k) != prev_data.get(k):
            log(f"Cambio rilevato in campo '{k}'")
            return True
    return False


def main():
    prev_data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    log(f"Stato precedente: cases={prev_data.get('cases')}, deaths={prev_data.get('deaths')}, "
        f"monitored={prev_data.get('monitored')}, ts={prev_data.get('ts')}")

    rss_items = fetch_rss_items()

    if not rss_items:
        log("Nessuna entry RSS rilevante: salto chiamata Ollama e non riscrivo data.json.")
        return 0

    system, user = build_prompt(prev_data, rss_items)

    log(f"Chiamo Ollama Cloud ({OLLAMA_MODEL})...")
    response_text = call_ollama(system, user)
    log(f"Risposta ricevuta ({len(response_text)} caratteri)")

    new_data = extract_json(response_text)
    new_data = merge_with_prev(new_data, prev_data)

    if not has_substantive_changes(new_data, prev_data):
        log("Output Ollama identico allo stato precedente (solo ts cambierebbe): non riscrivo data.json.")
        return 0

    new_data["ts"] = int(time.time() * 1000)

    DATA_PATH.write_text(
        json.dumps(new_data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    log(f"data.json scritto: cases={new_data.get('cases')}, deaths={new_data.get('deaths')}, "
        f"monitored={new_data.get('monitored')}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"[update] FATAL: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        sys.exit(1)
