#!/usr/bin/env python3
"""Validatore schema per data.json. Exit 0 se valido, 1 altrimenti.

Usato come gate finale nel workflow GitHub Actions: se l'LLM produce JSON
malformato o fuori schema, il workflow esce con errore e NON committa il file
— la dashboard continua a mostrare l'ultimo data.json valido.
"""
import json
import sys

ALLOWED_COLORS = {"#ef4444", "#f59e0b", "#22d3ee"}
ALLOWED_EVENT_TYPES = {"c", "w", "m", "d"}


def is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def is_number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def is_finite_number(x):
    return is_number(x) and x == x and x not in (float("inf"), float("-inf"))


class Validator:
    def __init__(self):
        self.errors = []

    def err(self, msg):
        self.errors.append(msg)

    def check_coord_pair(self, pair, path):
        if not isinstance(pair, list) or len(pair) != 2:
            self.err(f"{path}: deve essere lista di 2 elementi")
            return
        for v in pair:
            if not is_finite_number(v):
                self.err(f"{path}: coordinata non numerica finita")
                return

    def validate(self, d):
        if not isinstance(d, dict):
            self.err("root: deve essere oggetto")
            return

        if not is_int(d.get("ts")):
            self.err("ts: deve essere int (unix ms)")
        if not is_int(d.get("cases")):
            self.err("cases: deve essere int")
        if not is_int(d.get("deaths")):
            self.err("deaths: deve essere int")
        if not is_int(d.get("monitored")):
            self.err("monitored: deve essere int")
        if not is_number(d.get("cfr")):
            self.err("cfr: deve essere number")
        if not isinstance(d.get("ship"), str) or not d.get("ship"):
            self.err("ship: deve essere stringa non vuota")
        defcon = d.get("defcon")
        if not is_int(defcon) or defcon < 1 or defcon > 5:
            self.err("defcon: deve essere int 1-5")

        for k in ("country_updates", "new_countries", "route_updates",
                  "new_evacuations", "new_flights", "events"):
            if not isinstance(d.get(k), list):
                self.err(f"{k}: deve essere array (anche vuoto)")

        for i, cu in enumerate(d.get("country_updates", []) or []):
            if not isinstance(cu, dict):
                self.err(f"country_updates[{i}]: deve essere oggetto")
                continue
            iso = str(cu.get("iso", ""))
            if not iso.isdigit():
                self.err(f"country_updates[{i}].iso: deve essere stringa numerica")
            if cu.get("color") not in ALLOWED_COLORS:
                self.err(f"country_updates[{i}].color: invalido ({cu.get('color')!r})")
            if not isinstance(cu.get("note", ""), str):
                self.err(f"country_updates[{i}].note: deve essere stringa")

        for i, nc in enumerate(d.get("new_countries", []) or []):
            if not isinstance(nc, dict):
                self.err(f"new_countries[{i}]: deve essere oggetto")
                continue
            if not str(nc.get("iso", "")).isdigit():
                self.err(f"new_countries[{i}].iso: deve essere stringa numerica")
            if nc.get("color") not in ALLOWED_COLORS:
                self.err(f"new_countries[{i}].color: invalido")
            if not isinstance(nc.get("name_it", ""), str) or not nc.get("name_it"):
                self.err(f"new_countries[{i}].name_it: richiesto")
            if not is_finite_number(nc.get("lon")):
                self.err(f"new_countries[{i}].lon: numerico richiesto")
            if not is_finite_number(nc.get("lat")):
                self.err(f"new_countries[{i}].lat: numerico richiesto")

        for i, ru in enumerate(d.get("route_updates", []) or []):
            if not isinstance(ru, dict):
                self.err(f"route_updates[{i}]: deve essere oggetto")
                continue
            if not is_finite_number(ru.get("lon")) or not is_finite_number(ru.get("lat")):
                self.err(f"route_updates[{i}].lon/lat: numerici richiesti")

        for key in ("new_evacuations", "new_flights"):
            for i, item in enumerate(d.get(key, []) or []):
                if not isinstance(item, dict):
                    self.err(f"{key}[{i}]: deve essere oggetto")
                    continue
                self.check_coord_pair(item.get("from"), f"{key}[{i}].from")
                self.check_coord_pair(item.get("to"), f"{key}[{i}].to")
                if not isinstance(item.get("label", ""), str):
                    self.err(f"{key}[{i}].label: deve essere stringa")

        trend = d.get("trend_3d")
        if trend is not None:
            if not isinstance(trend, dict):
                self.err("trend_3d: deve essere oggetto se presente")
            else:
                for k in ("from_ts", "to_ts"):
                    if not is_int(trend.get(k)):
                        self.err(f"trend_3d.{k}: deve essere int (unix ms)")
                for k in ("cases_delta", "deaths_delta", "monitored_delta"):
                    if not is_int(trend.get(k)):
                        self.err(f"trend_3d.{k}: deve essere int (può essere negativo)")
                if not isinstance(trend.get("window_label", ""), str):
                    self.err("trend_3d.window_label: deve essere stringa")

        for i, ev in enumerate(d.get("events", []) or []):
            if not isinstance(ev, dict):
                self.err(f"events[{i}]: deve essere oggetto")
                continue
            if not isinstance(ev.get("date", ""), str) or not ev.get("date"):
                self.err(f"events[{i}].date: richiesta stringa non vuota")
            if not isinstance(ev.get("text", ""), str) or not ev.get("text"):
                self.err(f"events[{i}].text: richiesto stringa non vuota")
            if ev.get("type") not in ALLOWED_EVENT_TYPES:
                self.err(f"events[{i}].type: invalido ({ev.get('type')!r})")


def main():
    if len(sys.argv) < 2:
        print("Uso: validate_data.py <data.json>", file=sys.stderr)
        return 2

    path = sys.argv[1]
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[validate] {path}: parse error: {e}", file=sys.stderr)
        return 1

    v = Validator()
    v.validate(data)

    if v.errors:
        print(f"[validate] {path}: {len(v.errors)} errore/i:", file=sys.stderr)
        for e in v.errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(f"[validate] {path}: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
