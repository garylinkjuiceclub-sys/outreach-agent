#!/usr/bin/env python3
"""
Prospecting Agent
-----------------
Reads market config from Google Sheets, finds seed domains
(via DuckDuckGo search for top-ranking sites in each niche/GEO,
plus Kadaza for Nordic markets), then pulls referring domains
from each seed via the Ahrefs API.

Results are written to the Domains tab in Google Sheets.
Duplicate domains are automatically skipped.
"""

import os
import json
import time
import re
import requests
from datetime import datetime
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import gspread
from google.oauth2.service_account import Credentials

# ── Config ────────────────────────────────────────────────────────────────────
AHREFS_API_BASE   = "https://api.ahrefs.com/v3"
SHEET_ID          = "1MRQ2U1BVlM3HLrxdNjOs0Rqz9pK4323E22ODKSu2Dxs"
CONFIG_TAB        = "Config"
DOMAINS_TAB       = "Domains"

AHREFS_KEY        = os.environ["AHREFS_API_KEY"]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# Kadaza directory URLs for Nordic markets (no search API needed)
KADAZA_URLS = {
    "NO": "https://www.kadaza.no",
    "DK": "https://www.kadaza.dk",
    "FI": "https://www.kadaza.fi",
}

# ── Google Sheets ─────────────────────────────────────────────────────────────

def get_sheets_client():
    creds_json = os.environ["GOOGLE_SHEETS_CREDENTIALS"]
    creds_dict = json.loads(creds_json)
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds  = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)


def setup_sheets(client):
    """Create Config and Domains tabs if they don't already exist."""
    sheet = client.open_by_key(SHEET_ID)

    # ── Config tab ────────────────────────────────────────────────────────────
    try:
        config_ws = sheet.worksheet(CONFIG_TAB)
        print(f"✓ Found existing '{CONFIG_TAB}' tab")
    except gspread.WorksheetNotFound:
        print(f"Creating '{CONFIG_TAB}' tab...")
        config_ws = sheet.add_worksheet(CONFIG_TAB, rows=200, cols=10)
        config_ws.append_row([
            "Market", "TLD", "Search_Query", "Seeds",
            "DR_Min", "DR_Max", "Traffic_Min", "Active", "Notes"
        ])
        # Default market rows — Seeds column left blank (auto-discovered)
        defaults = [
            ["UK",  ".co.uk", "online casino UK",    "", "10", "80", "1000", "TRUE", ""],
            ["US",  ".com",   "online casino USA",   "", "10", "80", "1000", "TRUE", ""],
            ["RO",  ".ro",    "casino online Romania","","10", "80", "1000", "TRUE", ""],
            ["SE",  ".se",    "online casino Sverige","","10", "80", "1000", "TRUE", ""],
            ["NO",  ".no",    "",                    "", "10", "80", "1000", "TRUE", "Auto-seeds via Kadaza"],
            ["DK",  ".dk",    "",                    "", "10", "80", "1000", "TRUE", "Auto-seeds via Kadaza"],
            ["FI",  ".fi",    "",                    "", "10", "80", "1000", "TRUE", "Auto-seeds via Kadaza"],
        ]
        config_ws.append_rows(defaults)
        print("  → Default market rows added. Add manual seeds in the 'Seeds' column anytime.")

    # ── Domains tab ───────────────────────────────────────────────────────────
    try:
        domains_ws = sheet.worksheet(DOMAINS_TAB)
        print(f"✓ Found existing '{DOMAINS_TAB}' tab")
    except gspread.WorksheetNotFound:
        print(f"Creating '{DOMAINS_TAB}' tab...")
        domains_ws = sheet.add_worksheet(DOMAINS_TAB, rows=100000, cols=12)
        domains_ws.append_row([
            "Domain", "DR", "Traffic", "Market", "TLD",
            "Category", "Date_Added", "Contacted", "Email_Found", "Notes"
        ])
        print("  → Domains tab created.")

    return config_ws, domains_ws


def read_config(config_ws):
    """Return only active market rows from Config tab."""
    records = config_ws.get_all_records()
    active  = [r for r in records if str(r.get("Active", "")).upper() == "TRUE"]
    print(f"\n→ {len(active)} active market(s) found in config")
    return active


def get_existing_domains(domains_ws):
    """Return a set of already-stored domains (lowercase) to avoid duplicates."""
    values = domains_ws.col_values(1)[1:]   # Column A, skip header
    return set(v.strip().lower() for v in values if v.strip())


# ── Seed Discovery ────────────────────────────────────────────────────────────

def search_duckduckgo(query, max_results=20):
    """
    Search DuckDuckGo HTML for a query and return the top domain results.
    Used to find the best-ranking casino / niche sites per market.
    """
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

        print(f"    DuckDuckGo '{query}' → {len(domains)} seed(s) found")
    except Exception as e:
        print(f"    DuckDuckGo search failed: {e}")
    return domains


def get_kadaza_seeds(market, max_seeds=60):
    """
    Scrape Kadaza directory for a Nordic market to collect local seed domains.
    """
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

        print(f"    Kadaza {market} → {len(seeds)} seed(s) found")
    except Exception as e:
        print(f"    Kadaza scrape failed for {market}: {e}")
    return seeds


# ── Ahrefs API ────────────────────────────────────────────────────────────────

def get_referring_domains(seed, dr_min, dr_max, traffic_min):
    """
    Pull all referring domains for a seed domain from Ahrefs API,
    filtered by DR and traffic thresholds.
    Returns a list of dicts: {domain, dr, traffic}
    """
    results = []
    offset  = 0
    limit   = 1000

    while True:
        params = {
            "target":   seed,
            "mode":     "domain",
            "limit":    limit,
            "offset":   offset,
            "select":   "referring_domain,domain_rating_source,org_traffic",
            "where":    json.dumps({
                "and": [
                    {"field": "domain_rating_source", "is": ["gte", int(dr_min)]},
                    {"field": "domain_rating_source", "is": ["lte", int(dr_max)]},
                    {"field": "org_traffic",          "is": ["gte", int(traffic_min)]},
                ]
            }),
            "order_by": "domain_rating_source:desc",
        }
        headers = {
            "Authorization": f"Bearer {AHREFS_KEY}",
            "Accept":        "application/json",
        }

        try:
            resp = requests.get(
                f"{AHREFS_API_BASE}/site-explorer/referring-domains",
                headers=headers,
                params=params,
                timeout=30,
            )

            if resp.status_code == 429:
                print("    Rate limited — waiting 60s...")
                time.sleep(60)
                continue

            if resp.status_code != 200:
                print(f"    Ahrefs error {resp.status_code}: {resp.text[:200]}")
                break

            data    = resp.json()
            domains = data.get("referring_domains", [])

            for d in domains:
                results.append({
                    "domain":  d.get("referring_domain", "").lower().strip(),
                    "dr":      d.get("domain_rating_source", 0),
                    "traffic": d.get("org_traffic", 0),
                })

            if len(domains) < limit:
                break   # No more pages

            offset += limit
            time.sleep(0.5)

        except Exception as e:
            print(f"    Exception fetching Ahrefs data for {seed}: {e}")
            break

    return results


# ── Main ──────────────────────────────────────────────────────────────────────

def run():
    print("=" * 60)
    print("  PROSPECTING AGENT STARTING")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    client               = get_sheets_client()
    config_ws, domains_ws = setup_sheets(client)
    configs              = read_config(config_ws)
    existing             = get_existing_domains(domains_ws)

    print(f"\n→ {len(existing)} domain(s) already in sheet (will be skipped)")

    all_new_rows = []

    for cfg in configs:
        market      = cfg["Market"]
        tld         = cfg["TLD"]
        query       = str(cfg.get("Search_Query", "")).strip()
        manual_seeds = [s.strip() for s in str(cfg.get("Seeds", "")).split(",") if s.strip()]
        dr_min      = cfg.get("DR_Min",      10)
        dr_max      = cfg.get("DR_Max",      80)
        traffic_min = cfg.get("Traffic_Min", 1000)

        print(f"\n{'─'*50}")
        print(f"  Market: {market}  |  DR: {dr_min}–{dr_max}  |  Traffic: {traffic_min}+")
        print(f"{'─'*50}")

        # ── Build seed list ────────────────────────────────────────────────
        seeds = list(manual_seeds)

        if market in KADAZA_URLS:
            seeds += get_kadaza_seeds(market)
        elif query:
            seeds += search_duckduckgo(query, max_results=20)

        seeds = list(dict.fromkeys(seeds))  # Deduplicate, preserve order
        if not seeds:
            print(f"  ⚠ No seeds found for {market} — skipping")
            continue

        print(f"  → {len(seeds)} seed(s) to process")

        market_seen = set()
        market_new  = []

        for seed in seeds:
            print(f"  ↳ Ahrefs: referring domains for {seed} ...")
            domains = get_referring_domains(seed, dr_min, dr_max, traffic_min)

            for d in domains:
                domain = d["domain"]
                if not domain:
                    continue
                if domain in existing or domain in market_seen:
                    continue
                market_seen.add(domain)
                market_new.append([
                    domain,
                    d["dr"],
                    d["traffic"],
                    market,
                    tld,
                    "",                                      # Category (filled later)
                    datetime.now().strftime("%Y-%m-%d"),     # Date_Added
                    "No",                                    # Contacted
                    "No",                                    # Email_Found
                    "",                                      # Notes
                ])

            time.sleep(1)   # Be polite to Ahrefs API

        print(f"  ✓ {len(market_new)} new unique domain(s) found for {market}")
        all_new_rows.extend(market_new)

    # ── Write to Google Sheets ─────────────────────────────────────────────
    if all_new_rows:
        print(f"\n→ Writing {len(all_new_rows)} new domain(s) to Google Sheets...")
        batch = 500
        for i in range(0, len(all_new_rows), batch):
            chunk = all_new_rows[i : i + batch]
            domains_ws.append_rows(chunk, value_input_option="USER_ENTERED")
            print(f"  Written {min(i + batch, len(all_new_rows))} / {len(all_new_rows)}")
            time.sleep(1)
        print("✓ Done!")
    else:
        print("\n→ No new domains to write.")

    print("\n" + "=" * 60)
    print("  PROSPECTING AGENT COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    run()
