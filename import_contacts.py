"""
Import Contacts — Link Juice Club Database Importer
=====================================================
Reads your team's manually vetted CSV export (from Google Sheets) and
converts it into the outreach_contacts.csv format that send_emails.py reads.

Usage:
  1. Export your Google Sheet as CSV
  2. Place it in the repo root (or pass the path as an argument)
  3. Run: python import_contacts.py your_export.csv

It will:
  - Map your database columns to the pipeline format
  - Filter out domains already in output/sent_log.csv (never email twice)
  - Append new contacts to output/outreach_contacts.csv

Run manually or add to a GitHub Actions workflow.
"""

import csv, sys, os
from pathlib import Path

# ── File paths ────────────────────────────────────────────────────────────────
SENT_LOG        = "output/sent_log.csv"
CONTACTS_FILE   = "output/outreach_contacts.csv"

# ── Topic mapping ─────────────────────────────────────────────────────────────
# Maps your database's topic labels → pipeline template keys
TOPIC_MAP = {
    # Sports
    "sports news":                      "Sports",
    "sports":                           "Sports",
    "football":                         "Sports",
    "soccer":                           "Sports",
    "basketball":                       "Sports",
    "tennis":                           "Sports",
    "golf":                             "Sports",
    "rugby":                            "Sports",
    "cricket":                          "Sports",
    "athletics":                        "Sports",
    "motorsport":                       "Sports",
    "esports":                          "Gaming/eSports",
    "gaming":                           "Gaming/eSports",
    "gaming/esports":                   "Gaming/eSports",
    "video games":                      "Gaming/eSports",
    # Tech
    "technology and gadgets":           "Tech",
    "technology":                       "Tech",
    "tech":                             "Tech",
    "software":                         "Tech",
    "hardware":                         "Tech",
    "mobile":                           "Tech",
    "science and technology":           "Tech",
    # Finance
    "finance and fintech":              "Finance",
    "finance":                          "Finance",
    "fintech":                          "Finance",
    "business and finance":             "Finance",
    "economics":                        "Finance",
    "investing":                        "Finance",
    "stock market":                     "Finance",
    # Crypto
    "digital assets and crypto":        "Crypto",
    "crypto":                           "Crypto",
    "cryptocurrency":                   "Crypto",
    "blockchain":                       "Crypto",
    "bitcoin":                          "Crypto",
    # Gambling
    "gambling":                         "Gambling",
    "casino":                           "Gambling",
    "betting":                          "Gambling",
    "igaming":                          "Gambling",
    # Global News
    "global news and politics":         "Global News",
    "global news":                      "Global News",
    "world news":                       "Global News",
    "international news":               "Global News",
    "politics":                         "Global News",
    # General News
    "general news":                     "General News",
    "news":                             "General News",
    "local news":                       "General News",
    "regional news":                    "General News",
    # Entertainment
    "entertainment and celebrity":      "Entertainment",
    "entertainment":                    "Entertainment",
    "celebrity":                        "Entertainment",
    "music and reviews":                "Entertainment",
    "music":                            "Entertainment",
    "movies":                           "Entertainment",
    "tv":                               "Entertainment",
    "film":                             "Entertainment",
    "media and press services":         "Entertainment",
    # Travel
    "travel":                           "Travel",
    "travel blogs":                     "Travel",
    "travel and tourism":               "Travel",
    "tourism":                          "Travel",
    "lifestyle and travel":             "Travel",
    # Magazines
    "magazines":                        "Magazines",
    "magazine":                         "Magazines",
    "lifestyle":                        "Magazines",
    "fashion":                          "Magazines",
    "health":                           "Magazines",
    "food and culinary experiences":    "Magazines",
    "food":                             "Magazines",
    "personal blog and reflections":    "Magazines",
    "blog":                             "Magazines",
}

def map_topic(raw_topic: str) -> str:
    """Map a database topic string to a pipeline template key."""
    if not raw_topic:
        return "Unknown"
    key = raw_topic.strip().lower()
    # Exact match
    if key in TOPIC_MAP:
        return TOPIC_MAP[key]
    # Partial match — check if any known keyword appears in the topic
    for keyword, mapped in TOPIC_MAP.items():
        if keyword in key:
            return mapped
    return "Unknown"


def load_sent_domains() -> set:
    """Return set of domains already emailed (from sent_log.csv)."""
    sent = set()
    if Path(SENT_LOG).exists():
        with open(SENT_LOG, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                sent.add(row["domain"].strip().lower())
    return sent


def load_existing_contacts() -> set:
    """Return set of domains already in outreach_contacts.csv."""
    existing = set()
    if Path(CONTACTS_FILE).exists():
        with open(CONTACTS_FILE, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                existing.add(row["domain"].strip().lower())
    return existing


def import_csv(input_path: str):
    print(f"\n  Reading: {input_path}")

    sent_domains     = load_sent_domains()
    existing_domains = load_existing_contacts()
    skip_domains     = sent_domains | existing_domains

    print(f"  Already contacted / in queue: {len(skip_domains)} domains")

    new_contacts = []
    skipped = 0
    no_email = 0

    with open(input_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        # Normalise column headers (strip whitespace + newlines from multi-line headers)
        reader.fieldnames = [h.replace("\n", " ").strip() for h in reader.fieldnames]

        for row in reader:
            # Normalise all keys too
            row = {k.replace("\n", " ").strip(): v for k, v in row.items()}

            domain = row.get("Domain", "").strip().lower()
            if not domain:
                continue

            # Pick best email: prefer Webmaster Contact, fall back to Extra Contact
            email = row.get("Webmaster Contact", "").strip()
            if not email or "@" not in email:
                email = row.get("Webmaster Extra Contact", "").strip()
            if not email or "@" not in email:
                no_email += 1
                continue

            if domain in skip_domains:
                skipped += 1
                continue

            topic_raw = row.get("Website Topic", "").strip()
            topic     = map_topic(topic_raw)

            dr      = row.get("Ahrefs  Domain Rating", row.get("Ahrefs Domain Rating", "")).strip()
            traffic = row.get("Ahrefs  Organic Traffic", row.get("Ahrefs Organic Traffic", "")).strip()
            country = row.get("Main Country", "").strip()
            language= row.get("Domain Language", "").strip()

            new_contacts.append({
                "domain":         domain,
                "best_email":     email,
                "topic_category": topic,
                "dr":             dr,
                "traffic":        traffic,
                "country":        country,
                "language":       language,
                "source":         "manual_import",
            })

            skip_domains.add(domain)  # prevent duplicates within this import

    if not new_contacts:
        print(f"\n  No new contacts to import.")
        print(f"  Skipped (already contacted): {skipped}")
        print(f"  Skipped (no email found):    {no_email}")
        return

    # Write to outreach_contacts.csv
    Path(CONTACTS_FILE).parent.mkdir(parents=True, exist_ok=True)
    file_exists = Path(CONTACTS_FILE).exists()
    fieldnames  = ["domain", "best_email", "topic_category", "dr", "traffic",
                   "country", "language", "source"]

    with open(CONTACTS_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerows(new_contacts)

    print(f"\n  ✓ Imported:  {len(new_contacts)} new contacts")
    print(f"  Skipped (already contacted): {skipped}")
    print(f"  Skipped (no email found):    {no_email}")
    print(f"  Output → {CONTACTS_FILE}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_contacts.py path/to/your_export.csv")
        sys.exit(1)
    import_csv(sys.argv[1])
