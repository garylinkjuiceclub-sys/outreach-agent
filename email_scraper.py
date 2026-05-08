"""
LJC Outreach - Deep Email Scraper v2.2
========================================
Fixes vs v2.1:
  - Fixed SyntaxError in extract_emails (strip call with special chars)
  - Uses raw strings for all regex patterns
  - Filters image filenames, retina patterns, file-extension TLDs
  - Fresh session per domain to beat WAF rate limiting
  - Deep editorial paths (/about/editorial-team, /meet-the-team etc)

OUTPUT: domain, primary_email, email_2, email_3, all_emails, pages_checked, status, date_scraped
"""

import csv
import re
import time
import logging
from datetime import datetime
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

INPUT_FILE  = "domains_input.csv"
OUTPUT_FILE = "emails_output.csv"

TIMEOUT       = 12
MAX_PAGES     = 15
REQUEST_DELAY = 0.8

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-GB,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

CONTACT_PATHS = [
    "/contact", "/contact-us", "/contact_us", "/contactus",
    "/about", "/about-us", "/about_us", "/aboutus",
    "/advertise", "/advertise-with-us", "/advertising",
    "/partnerships", "/editorial", "/editorial-team", "/editorial-staff",
    "/about/editorial-team", "/about/editorial", "/about/contact",
    "/about/contact-us", "/about/staff", "/about/team", "/about/us",
    "/team", "/our-team", "/meet-the-team", "/who-we-are",
    "/staff", "/writers", "/contribute", "/write-for-us", "/submit",
    "/press", "/media", "/media-kit",
    "/info", "/reach-us", "/get-in-touch",
    "/nous-contacter", "/contactez-nous", "/a-propos",
    "/publicite", "/kontakt", "/redaction", "/annonceurs",
]

FILE_EXTENSIONS = {
    "png", "jpg", "jpeg", "gif", "svg", "webp", "ico", "bmp", "tiff",
    "css", "js", "json", "xml", "html", "htm",
    "woff", "woff2", "ttf", "eot", "otf",
    "pdf", "zip", "gz", "tar", "rar",
    "mp4", "mp3", "avi", "mov", "webm",
}

CONTACT_LINK_KEYWORDS = [
    "contact", "about", "advertise", "advertising", "editorial",
    "team", "staff", "press", "media", "partner", "write for",
    "contribute", "submit", "reach", "get in touch", "redaction",
    "publicite", "annonce", "nous contacter", "a propos", "equipe",
    "info", "newsletter",
]

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

IMAGE_LOCAL_RE  = re.compile(r"\.(png|jpg|jpeg|gif|svg|webp|css|js|ico|woff|ttf|pdf|mp4|mp3)$")
RETINA_RE       = re.compile(r"\d+x\d+")
DOMAIN_DIM_RE   = re.compile(r"^\d+[xk2-9]")
PLACEHOLDER_RE  = re.compile(r"^(john|jane|user|name|email|your|votre|example)\.")


def score_email(email):
    if "@" not in email:
        return -999
    parts = email.split("@", 1)
    local = parts[0].lower()
    domain = parts[1].lower()

    BLACKLIST_LOCALS = {
        "noreply", "no-reply", "donotreply", "do-not-reply",
        "mailer-daemon", "postmaster", "bounce", "bounces",
        "unsubscribe", "notifications", "notify", "alert", "alerts",
        "newsletter", "newsletters", "subscribe", "subscriptions",
        "feedback", "survey", "abuse", "spam", "security",
        "privacy", "legal", "careers", "jobs", "recruitment",
        "hr", "finance", "accounts", "billing", "invoice",
        "orders", "sales", "shop", "store", "ecommerce",
        "example", "test", "demo", "votre", "your",
    }
    BLACKLIST_DOMAINS = {
        "example.com", "test.com", "domain.com", "email.com",
        "sentry.io", "wixpress.com", "squarespace.com",
        "doe.com", "clean.cloud", "yourwebsite.com", "test.test",
    }

    if local in BLACKLIST_LOCALS:
        return -999
    if domain in BLACKLIST_DOMAINS:
        return -999
    if IMAGE_LOCAL_RE.search(local):
        return -999
    if RETINA_RE.search(local):
        return -999
    tld = domain.split(".")[-1].lower() if "." in domain else ""
    if tld in FILE_EXTENSIONS:
        return -999
    if DOMAIN_DIM_RE.search(domain):
        return -999
    if PLACEHOLDER_RE.search(local):
        return -999

    TIER1 = [
        "editor", "editorial", "partnerships", "partnership", "partner",
        "advertise", "advertising", "ads", "advert",
        "media", "press", "pr", "links", "seo",
        "contribute", "contributions", "submit", "tips",
        "news", "newsroom", "newsdesk", "redaction", "desk",
    ]
    for kw in TIER1:
        if kw in local:
            return 100

    TIER2 = [
        "contact", "hello", "hi", "reach", "enquir", "inquir",
        "general", "mail", "administration", "admin", "webmaster", "staff",
    ]
    for kw in TIER2:
        if kw in local:
            return 60

    for kw in ["info", "office", "team", "write"]:
        if kw in local:
            return 30

    if "gmail.com" in domain or "yahoo." in domain or "outlook." in domain:
        return 20

    return 10


def extract_emails(text):
    raw = EMAIL_RE.findall(text)
    cleaned = []
    for e in raw:
        # Strip common trailing/leading punctuation safely
        e = e.lower()
        while e and e[-1] in ".,;:\"'>)":
            e = e[:-1]
        while e and e[0] in ".,;:\"'<(":
            e = e[1:]
        if len(e) > 6 and "@" in e and "." in e.split("@")[-1]:
            cleaned.append(e)
    return list(set(cleaned))


def fetch(url, session):
    try:
        resp = session.get(url, timeout=TIMEOUT, headers=HEADERS, allow_redirects=True)
        if resp.status_code == 200:
            return resp.text
        return None
    except Exception:
        return None


def find_contact_links(html, base_url):
    soup = BeautifulSoup(html, "lxml")
    found = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        text = a.get_text(strip=True).lower()
        combined = (href + " " + text).lower()
        if any(kw in combined for kw in CONTACT_LINK_KEYWORDS):
            abs_url = urljoin(base_url, href)
            if urlparse(abs_url).netloc == urlparse(base_url).netloc:
                found.append(abs_url)
    seen = set()
    unique = []
    for u in found:
        if u not in seen:
            seen.add(u)
            unique.append(u)
    return unique


def make_session():
    s = requests.Session()
    s.max_redirects = 5
    s.headers.update(HEADERS)
    return s


def scrape_domain(domain, session):
    domain = re.sub(r"^https?://", "", domain.strip().lower())
    domain = re.sub(r"^www\.", "", domain).rstrip("/")
    base = "https://www." + domain

    all_emails = {}
    pages_checked = []
    status = "error"

    def add_emails(text):
        for e in extract_emails(text):
            s = score_email(e)
            if s > -999:
                all_emails[e] = max(all_emails.get(e, s), s)

    html = (
        fetch(base, session) or
        fetch("https://" + domain, session) or
        fetch("http://www." + domain, session)
    )
    if html:
        add_emails(html)
        pages_checked.append(base)
        status = "scraped"
        contact_links = find_contact_links(html, base)
    else:
        contact_links = []

    checked = set(pages_checked)

    for path in CONTACT_PATHS:
        if len(pages_checked) >= MAX_PAGES:
            break
        url = base + path
        if url in checked:
            continue
        time.sleep(REQUEST_DELAY * 0.4)
        h = fetch(url, session)
        if h:
            add_emails(h)
            pages_checked.append(url)
            checked.add(url)

    for url in contact_links:
        if len(pages_checked) >= MAX_PAGES:
            break
        if url in checked:
            continue
        time.sleep(REQUEST_DELAY * 0.4)
        h = fetch(url, session)
        if h:
            add_emails(h)
            pages_checked.append(url)
            checked.add(url)

    ranked = [e for e, _ in sorted(all_emails.items(), key=lambda x: x[1], reverse=True)]

    if not ranked and status == "scraped":
        status = "no_email_found"

    return {
        "domain":        domain,
        "primary_email": ranked[0] if len(ranked) > 0 else "",
        "email_2":       ranked[1] if len(ranked) > 1 else "",
        "email_3":       ranked[2] if len(ranked) > 2 else "",
        "all_emails":    " | ".join(ranked),
        "pages_checked": len(pages_checked),
        "status":        status if not ranked else "scraped",
        "date_scraped":  datetime.now().strftime("%d/%m/%Y"),
    }


def load_domains(path):
    domains = []
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            for i, row in enumerate(csv.reader(f)):
                if not row:
                    continue
                cell = row[0].strip()
                if i == 0 and cell.lower() in ("domain", "domains", "website", "url"):
                    continue
                if cell:
                    domains.append(cell)
    except FileNotFoundError:
        logging.error("Input file not found: " + path)
    return domains


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(message)s",
        datefmt="%H:%M:%S",
    )
    domains = load_domains(INPUT_FILE)
    if not domains:
        logging.error("No domains found. Exiting.")
        return

    logging.info("Loaded " + str(len(domains)) + " domains")
    fieldnames = [
        "domain", "primary_email", "email_2", "email_3",
        "all_emails", "pages_checked", "status", "date_scraped",
    ]

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as out_f:
        writer = csv.DictWriter(out_f, fieldnames=fieldnames)
        writer.writeheader()

        for i, domain in enumerate(domains, 1):
            logging.info("[" + str(i) + "/" + str(len(domains)) + "] " + domain)
            session = make_session()
            try:
                result = scrape_domain(domain, session)
            except Exception as e:
                logging.warning("  Error: " + str(e))
                result = {
                    "domain":        domain,
                    "primary_email": "",
                    "email_2":       "",
                    "email_3":       "",
                    "all_emails":    "",
                    "pages_checked": 0,
                    "status":        "error",
                    "date_scraped":  datetime.now().strftime("%d/%m/%Y"),
                }

            writer.writerow(result)
            out_f.flush()

            msg = "  -> " + result["status"]
            if result["primary_email"]:
                msg += " | " + result["primary_email"]
                extras = [e for e in [result["email_2"], result["email_3"]] if e]
                if extras:
                    msg += " | also: " + ", ".join(extras)
            logging.info(msg)
            time.sleep(REQUEST_DELAY)

    logging.info("Done. Saved to " + OUTPUT_FILE)


if __name__ == "__main__":
    main()
