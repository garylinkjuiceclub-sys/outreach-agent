#!/usr/bin/env python3
"""
Email Scraper Agent (Agent 2)
------------------------------
INPUT:  domains_input.csv  — one domain per line, no header needed
OUTPUT: emails_output.csv  — domain, email, status, date_scraped

To use:
  1. Edit domains_input.csv (paste your list of domains)
  2. Commit the file to GitHub
  3. Go to Actions → Email Scraper Agent → Run workflow
  4. Download emails_output.csv from the run's Artifacts section
"""

import csv
import os
import re
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

INPUT_FILE  = "domains_input.csv"
OUTPUT_FILE = "emails_output.csv"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

CONTACT_PATHS = [
    "/contact", "/contact-us", "/about", "/about-us",
    "/advertise", "/advertise-with-us", "/write-for-us",
    "/submit-guest-post", "/guest-post", "/contribute", "/team", "/",
]

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", re.IGNORECASE)

JUNK_DOMAINS = {
    "example.com","sentry.io","wixpress.com","cloudflare.com",
    "google.com","facebook.com","twitter.com","instagram.com",
    "jquery.com","w3.org","schema.org","linkedin.com","youtube.com",
    "amazonaws.com","wp.com","wordpress.com","gravatar.com",
}

HR = "-" * 55


def load_domains(path):
    domains = []
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            sample = f.read(1024)
            f.seek(0)
            has_header = any(h in sample.lower() for h in ("domain","url","website","site"))
            reader = csv.DictReader(f) if has_header else csv.reader(f)
            for row in reader:
                raw = (row.get("domain") or row.get("Domain") or row.get("url") or
                       row.get("URL") or row.get("website") or row.get("Website") or
                       (list(row.values())[0] if isinstance(row, dict) else row[0]))
                if not raw:
                    continue
                domain = raw.strip().lower().replace("https://","").replace("http://","").rstrip("/")
                if domain:
                    domains.append(domain)
    except FileNotFoundError:
        print(f"[!] Input file not found: {path}")
    return domains


def clean_email(email):
    email = email.lower().strip().rstrip(".")
    if not email or "@" not in email:
        return None
    domain = email.split("@")[-1]
    if any(j in domain for j in JUNK_DOMAINS):
        return None
    if len(email) > 80 or len(domain) < 4:
        return None
    if re.search(r"\.(png|jpg|gif|svg|css|js|ico|woff|ttf)$", domain):
        return None
    return email


def extract_emails(html):
    soup = BeautifulSoup(html, "html.parser")
    found = set()
    for a in soup.find_all("a", href=True):
        if a["href"].lower().startswith("mailto:"):
            c = clean_email(a["href"][7:].split("?")[0].strip())
            if c: found.add(c)
    for m in EMAIL_RE.findall(soup.get_text(" ")):
        c = clean_email(m)
        if c: found.add(c)
    for m in EMAIL_RE.findall(html):
        c = clean_email(m)
        if c: found.add(c)
    return found


def fetch(url, timeout=10):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        if r.status_code == 200 and "text/html" in r.headers.get("Content-Type",""):
            return r.text
    except Exception:
        pass
    return None


def scrape(domain):
    base = f"https://{domain}"
    domain_root = re.sub(r"^www\.", "", domain)
    pool = set()
    for path in CONTACT_PATHS:
        html = fetch(base + path)
        if html:
            pool.update(extract_emails(html))
        time.sleep(0.3)
    own = {e for e in pool if domain_root in e.split("@")[-1]}
    if own:
        for prefix in ["editor","editorial","contact","hello","info","admin"]:
            for e in sorted(own):
                if e.startswith(prefix + "@"):
                    return e, "scraped"
        return sorted(own)[0], "scraped"
    if pool:
        return sorted(pool)[0], "scraped"
    return f"info@{domain_root}", "pattern"


def run():
    print("=" * 55)
    print("  EMAIL SCRAPER AGENT")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)
    domains = load_domains(INPUT_FILE)
    if not domains:
        print(f"\n[!] No domains found in {INPUT_FILE}. Exiting.")
        return
    seen = set()
    unique = [d for d in domains if not (d in seen or seen.add(d))]
    print(f"\n-> {len(unique)} unique domain(s) loaded")
    results = []
    scraped = pattern = errors = 0
    print(f"\n{HR}")
    for i, domain in enumerate(unique, 1):
        print(f"  [{i}/{len(unique)}] {domain} ...", end=" ", flush=True)
        try:
            email, status = scrape(domain)
            results.append({"domain": domain, "email": email, "status": status,
                            "date_scraped": datetime.now().strftime("%Y-%m-%d")})
            print(f"{'FOUND' if status == 'scraped' else 'pattern'}: {email}")
            if status == "scraped": scraped += 1
            else: pattern += 1
        except Exception as e:
            print(f"ERROR: {e}")
            results.append({"domain": domain, "email": "", "status": "error",
                            "date_scraped": datetime.now().strftime("%Y-%m-%d")})
            errors += 1
        time.sleep(0.5)
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["domain","email","status","date_scraped"])
        writer.writeheader()
        writer.writerows(results)
    print(f"\n{HR}")
    print(f"  Done. Results → {OUTPUT_FILE}")
    print(f"  Real emails: {scraped}  |  Pattern: {pattern}  |  Errors: {errors}")
    print("=" * 55)
    print("\n  Download emails_output.csv from the Actions Artifacts.")

if __name__ == "__main__":
    run()
