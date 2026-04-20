#!/usr/bin/env python3
"""
Prospecting Agent
-----------------
Reads market config from Google Sheets (via Apps Script web app),
finds seed domains via DuckDuckGo search (UK/US/RO/SE) or Kadaza (NO/DK/FI),
then pulls referring domains from the Ahrefs API.

Results are written back to the Domains tab via the Apps Script web app.
No Google Cloud account or service account needed.
"""

import os
import json
import time
import requests
from datetime import datetime
from urllib.parse import urlparse
from bs4 import BeautifulSoup

# ── Environment variables (set as GitHub Secrets) ─────────────────────────────
AHREFS_KEY     = os.environ["AHREFS_API_KEY"]
SHEETS_URL     = os.environ["SHEETS_API_URL"]      # Apps Script web app URL
SHEETS_TOKEN   = os.environ["SHEETS_API_TOKEN"]    # Secret token from setup()

# Ahrefs v3 API
AHREFS_API_BASE = "https://api.ahrefs.com/v3"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

KADAZA_URLS = {
    "NO": "https://www.kadaza.no",
    "DK": "https://www.kadaza.dk",
    "FI": "https://www.kadaza.fi",
}

# ── Google Sheets (via Apps Script) ──────────────────────────────────────────

def sheets_get(action, **kwargs):
    params = {"token": SHEETS_TOKEN, "action": action, **kwargs}
    resp   = requests.get(SHEETS_URL, params=params, timeout=30)
    return resp.json()


def sheets_post(action, **kwargs):
    payload = {"token": SHEETS_TOKEN, "action": action, **kwargs}
    resp    = requests.post(SHEETS_URL, json=payload, timeout=60)
    return resp.json()


def read_config():
    print("Reading config from Google Sheets...")
    data   = sheets_get("config")
    rows   = data.get("config", [])
    active = [r for r in rows if str(r.get("Active", "")).upper() == "TRUE"]
    print(f"\u2192 {len(active)} active market(s)")
    return active


def get_existing_domains():
    print("Fetching existing domains for deduplication...")
    data    = sheets_post("get_existing_domains")
    domains = set(d.strip().lower() for d in data.get("domains", []) if d.strip())
    print(f"\u2192 {len(domains)} domain(s) already in sheet")
    return domains


def write_domains(rows):
    total   = len(rows)
    batch   = 500
    written = 0
    for i in range(0, total, batch):
        chunk  = rows[i : i + batch]
        result = sheets_post("write_domains", rows=chunk)
        written += result.get("written", 0)
        print(f"  Written {min(i + batch, total)} / {total}")
        time.sleep(1)
    return written


# ── Seed Discovery ────────────────────────────────────────────────────────────

def search_duckduckgo(query, max_results=20):
    domains = []
    try:
        url  = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        for a in soup.select("a.result__url"):
            href = a.get("href", "")
            if href.startswith("http"):
                domain = urlparse(href).netloc.replace("www.", "")
                if domain and domain not in domains:
                    domains.append(domain)
            if len(domains) >= max_results:
                break
        print(f"    DuckDuckGo '{query}' \u2192 {len(domains)} seed(s)")
    except Exception as e:
        print(f"    DuckDuckGo failed: {e}")
    return domains


def get_kadaza_seeds(market, max_seeds=60):
    base_url = KADAZA_URLS.get(market)
    if not base_url:
        return []
    seeds = []
    try:
        resp = requests.get(base_url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.startswith("http") and base_url not in href:
                domain = urlparse(href).netloc.replace("www.", "")
                if domain and len(domain) > 4 and domain not in seeds:
                    seeds.append(domain)
            if len(seeds) >= max_seeds:
                break
        print(f"    Kadaza {market} \u2192 {len(seeds)} seed(s)")
    except Exception as e:
        print(f"    Kadaza failed for {market}: {e}")
    return seeds


# ── Ahrefs API ────────────────────────────────────────────────────────────────

def get_referring_domains(seed, dr_min, dr_max, traffic_min):
    """
    Fetches referring domains using Ahrefs API v3.
    Filtering is done in Python after fetch to avoid server-side filter issues.
    """
    results = []
    offset  = 0
    limit   = 1000

    while True:
        headers = {
            "Authorization": f"Bearer {AHREFS_KEY}",
            "Accept":        "application/json",
        }

        params = {
            "target":   seed,
            "mode":     "domain",
            "limit":    limit,
            "offset":   offset,
            "select":   "domain,domain_rating,traffic_domain",
        }

        try:
            resp = requests.get(
                f"{AHREFS_API_BASE}/site-explorer/refdomains",
                headers=headers,
                params=params,
                timeout=30,
            )

            if resp.status_code == 429:
                print("    Rate limited \u2014 waiting 60s...")
                time.sleep(60)
                continue

            if resp.status_code != 200:
                print(f"    Ahrefs error {resp.status_code}: {resp.text[:500]}")
                break

            data = resp.json()

            if offset == 0:
                # Log full response structure on first call for debugging
                print(f"    RAW RESPONSE KEYS: {list(data.keys())}")
                print(f"    RAW SAMPLE: {json.dumps(data)[:500]}")

            # Try both possible response keys
            domains = data.get("refdomains") or data.get("referring_domains") or []

            # If still empty, check if data itself is a list or has other keys
            if not domains and isinstance(data, dict):
                for k, v in data.items():
                    if isinstance(v, list) and len(v) > 0:
                        print(f"    Found list under key '{k}': {len(v)} items")
                        domains = v
                        break

            print(f"    Page offset={offset}: {len(domains)} raw domains returned")

            passed = 0
            for d in domains:
                domain  = d.get("domain", "").lower().strip()
                dr      = int(d.get("domain_rating", 0) or 0)
                traffic = int(d.get("traffic_domain", 0) or 0)
                if domain and dr_min <= dr <= dr_max and traffic >= traffic_min:
                    results.append({"domain": domain, "dr": dr, "traffic": traffic})
                    passed += 1

            print(f"    \u2192 {passed} passed filters (DR {dr_min}-{dr_max}, traffic {traffic_min}+), {len(results)} total")

            if len(domains) < limit:
                break

            offset += limit
            time.sleep(0.5)

        except Exception as e:
            print(f"    Exception for {seed}: {e}")
            break

    return results


# ── Main ──────────────────────────────────────────────────────────────────────

def run():
    print("=" * 60)
    print("  PROSPECTING AGENT STARTING")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    configs  = read_config()
    existing = get_existing_domains()
    all_new_rows = []

    for cfg in configs:
        market       = cfg["Market"]
        tld          = cfg["TLD"]
        query        = str(cfg.get("Search_Query", "")).strip()
        manual_seeds = [s.strip() for s in str(cfg.get("Seeds", "")).split(",") if s.strip()]
        dr_min       = int(cfg.get("DR_Min",      10))
        dr_max       = int(cfg.get("DR_Max",      80))
        traffic_min  = int(cfg.get("Traffic_Min", 1000))

        print(f"\n{'\u2500'*50}")
        print(f"  Market: {market}  |  DR: {dr_min}\u2013{dr_max}  |  Traffic: {traffic_min}+")
        print(f"{'\u2500'*50}")

        seeds = list(manual_seeds)
        if market in KADAZA_URLS:
            seeds += get_kadaza_seeds(market)
        elif query:
            seeds += search_duckduckgo(query, max_results=20)

        seeds = list(dict.fromkeys(seeds))

        if not seeds:
            print(f"  \u26a0 No seeds found for {market} \u2014 skipping")
            continue

        print(f"  \u2192 {len(seeds)} seed(s) to process")

        market_seen = set()
        market_rows = []

        for seed in seeds:
            print(f"  \u21b3 Ahrefs: {seed} ...")
            domains = get_referring_domains(seed, dr_min, dr_max, traffic_min)
            for d in domains:
                domain = d["domain"]
                if not domain or domain in existing or domain in market_seen:
                    continue
                market_seen.add(domain)
                market_rows.append([
                    domain,
                    d["dr"],
                    d["traffic"],
                    market,
                    tld,
                    "",
                    datetime.now().strftime("%Y-%m-%d"),
                    "No",
                    "No",
                    "",
                ])
            time.sleep(1)

        print(f"  \u2713 {len(market_rows)} new domain(s) for {market}")
        all_new_rows.extend(market_rows)

    if all_new_rows:
        print(f"\n\u2192 Writing {len(all_new_rows)} new domain(s) to Google Sheets...")
        write_domains(all_new_rows)
        print("\u2713 Done!")
    else:
        print("\n\u2192 No new domains found.")

    print("\n" + "=" * 60)
    print("  PROSPECTING AGENT COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    run()
