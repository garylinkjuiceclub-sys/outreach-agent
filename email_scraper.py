"""
LJC Outreach - Deep Email Scraper v3.0
========================================
Phase 1 (all domains, fast):
  - Rotating user agents + realistic headers
  - Cloudflare email decode (data-cfemail / cf_email obfuscation)
  - Homepage + known contact paths + sitemap.xml discovery
  - Follow contact-type links from homepage

Phase 2 (fallback if no emails, medium):
  - Wayback Machine (web.archive.org) for cached contact pages
  - Google Custom Search API (if GOOGLE_API_KEY + GOOGLE_CSE_ID set)

Phase 3 (fallback if still no emails, slow):
  - Playwright headless browser for JS-rendered sites

Phase 4 (final fallback):
  - Hunter.io domain search API (if HUNTER_API_KEY set)

Post-processing:
  - SMTP verification on top candidates (if ENABLE_SMTP_VERIFY=true)

ENV VARS (set as GitHub Secrets or locally):
  HUNTER_API_KEY      â Hunter.io API key (optional)
  GOOGLE_API_KEY      â Google Custom Search API key (optional)
  GOOGLE_CSE_ID       â Google Custom Search Engine ID (optional)
  ENABLE_PLAYWRIGHT   â "true"/"false" (default: true)
  ENABLE_SMTP_VERIFY  â "true"/"false" (default: true)

OUTPUT: domain, primary_email, email_2, email_3, all_emails,
        pages_checked, source, status, date_scraped
"""

import csv
import os
import re
import random
import socket
import time
import logging
from datetime import datetime
from urllib.parse import urljoin, urlparse, quote_plus

import requests
from bs4 import BeautifulSoup

try:
    import dns.resolver
    HAS_DNS = True
except ImportError:
    HAS_DNS = False

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

INPUT_FILE  = "domains_input.csv"
OUTPUT_FILE = "emails_output.csv"

TIMEOUT       = 12
MAX_PAGES     = 20
BASE_DELAY    = 0.6

ENABLE_PLAYWRIGHT  = os.environ.get("ENABLE_PLAYWRIGHT", "true").lower() == "true"
ENABLE_SMTP_VERIFY = os.environ.get("ENABLE_SMTP_VERIFY", "true").lower() == "true"
HUNTER_API_KEY     = os.environ.get("HUNTER_API_KEY", "")
GOOGLE_API_KEY     = os.environ.get("GOOGLE_API_KEY", "")
GOOGLE_CSE_ID      = os.environ.get("GOOGLE_CSE_ID", "")

USER_AGENTS = [
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) "
        "Gecko/20100101 Firefox/125.0"
    ),
    (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/17.4.1 Safari/605.1.15"
    ),
]

CONTACT_PATHS = [
    "/contact", "/contact-us", "/contact_us", "/contactus",
    "/about", "/about-us", "/about_us", "/aboutus",
    "/advertise", "/advertise-with-us", "/advertising",
    "/partnerships", "/editorial", "/editorial-team", "/editorial-staff",
    "/about/editorial-team", "/about/editorial", "/about/contact",
    "/about/contact-us", "/about/staff", "/about/team", "/about/us",
    "/team", "/our-team", "/meet-the-team", "/who-we-are",
    "/staff", "/writers", "/contribute", "/write-for-us", "/submit",
    "/press", "/media", "/media-kit", "/media-enquiries",
    "/info", "/reach-us", "/get-in-touch",
    "/nous-contacter", "/contactez-nous", "/a-propos",
    "/publicite", "/kontakt", "/redaction", "/annonceurs",
    "/about/the-team", "/company", "/our-story",
]

CONTACT_KEYWORDS = [
    "contact", "about", "advertise", "advertising", "editorial",
    "team", "staff", "press", "media", "partner", "write for",
    "contribute", "submit", "reach", "get in touch", "redaction",
    "publicite", "annonce", "nous contacter", "a propos", "equipe",
    "info", "newsletter",
]

SITEMAP_KEYWORDS = [
    "contact", "about", "advertise", "editorial",
    "team", "staff", "press", "media", "partner",
]

FILE_EXTENSIONS = {
    "png", "jpg", "jpeg", "gif", "svg", "webp", "ico", "bmp", "tiff",
    "css", "js", "json", "xml", "html", "htm",
    "woff", "woff2", "ttf", "eot", "otf",
    "pdf", "zip", "gz", "tar", "rar",
    "mp4", "mp3", "avi", "mov", "webm",
}

EMAIL_RE        = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
IMAGE_LOCAL_RE  = re.compile(r"\.(png|jpg|jpeg|gif|svg|webp|css|js|ico|woff|ttf|pdf|mp4|mp3)$")
RETINA_RE       = re.compile(r"\d+x\d+")
DOMAIN_DIM_RE   = re.compile(r"^\d+[xk2-9]")
PLACEHOLDER_RE  = re.compile(r"^(john|jane|user|name|email|your|votre|example)\.")
CF_EMAIL_RE     = re.compile(r'data-cfemail="([0-9a-fA-F]+)"')


def decode_cf_email(encoded):
    try:
        key = int(encoded[:2], 16)
        email = "".join(
            chr(int(encoded[i:i+2], 16) ^ key)
            for i in range(2, len(encoded), 2)
        )
        return email if "@" in email else None
    except Exception:
        return None


def score_email(email):
    if "@" not in email:
        return -999
    parts = email.split("@", 1)
    local  = parts[0].lower()
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
    if local in BLACKLIST_LOCALS: return -999
    if domain in BLACKLIST_DOMAINS: return -999
    if IMAGE_LOCAL_RE.search(local): return -999
    if RETINA_RE.search(local): return -999
    tld = domain.split(".")[-1].lower() if "." in domain else ""
    if tld in FILE_EXTENSIONS: return -999
    if DOMAIN_DIM_RE.search(domain): return -999
    if PLACEHOLDER_RE.search(local): return -999
    TIER1 = ["editor", "editorial", "partnerships", "partnership", "partner",
             "advertise", "advertising", "ads", "advert", "media",
             "press", "pr", "links", "seo", "contribute", "submit",
             "tips", "news", "newsroom", "newsdesk", "redaction", "desk"]
    for kw in TIER1:
        if kw in local: return 100
    TIER2 = ["contact", "hello", "hi", "reach", "enquir", "inquir",
             "general", "mail", "administration", "admin", "webmaster", "staff"]
    for kw in TIER2:
        if kw in local: return 60
    for kw in ["info", "office", "team", "write"]:
        if kw in local: return 30
    if "gmail.com" in domain or "yahoo." in domain or "outlook." in domain:
        return 20
    return 10


def extract_emails(html_or_text):
    candidates = []
    for encoded in CF_EMAIL_RE.findall(html_or_text):
        decoded = decode_cf_email(encoded)
        if decoded:
            candidates.append(decoded.lower())
    raw = EMAIL_RE.findall(html_or_text)
    for e in raw:
        e = e.lower()
        while e and e[-1] in ".,;:\"'>)":
            e = e[:-1]
        while e and e[0] in ".,;:\"'<(":
            e = e[1:]
        if len(e) > 6 and "@" in e and "." in e.split("@")[-1]:
            candidates.append(e)
    return list(set(candidates))


def make_headers(referer=None):
    ua = random.choice(USER_AGENTS)
    h = {
        "User-Agent": ua,
        "Accept-Language": "en-GB,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "DNT": "1",
    }
    if referer:
        h["Referer"] = referer
    return h


def make_session():
    s = requests.Session()
    s.max_redirects = 5
    return s


def fetch(url, session, referer=None):
    try:
        resp = session.get(url, timeout=TIMEOUT, headers=make_headers(referer), allow_redirects=True)
        if resp.status_code == 200:
            return resp.text
        return None
    except Exception:
        return None


def jitter():
    time.sleep(BASE_DELAY + random.uniform(0.0, 0.8))


def find_contact_links(html, base_url):
    soup = BeautifulSoup(html, "lxml")
    found = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        text = a.get_text(strip=True).lower()
        combined = (href + " " + text).lower()
        if any(kw in combined for kw in CONTACT_KEYWORDS):
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


def get_sitemap_urls(domain, session):
    candidates = [
        "https://www." + domain + "/sitemap.xml",
        "https://www." + domain + "/sitemap_index.xml",
        "https://" + domain + "/sitemap.xml",
        "https://www." + domain + "/robots.txt",
    ]
    found = []
    for url in candidates:
        html = fetch(url, session)
        if not html:
            continue
        sub_sitemaps = re.findall(r"<sitemap>\s*<loc>(.*?)</loc>", html)
        for sm in sub_sitemaps[:3]:
            sm_html = fetch(sm.strip(), session)
            if sm_html:
                html += sm_html
        for loc in re.findall(r"<loc>(.*?)</loc>", html):
            loc = loc.strip()
            if any(kw in loc.lower() for kw in SITEMAP_KEYWORDS):
                found.append(loc)
        if "robots.txt" in url:
            for sm_url in re.findall(r"(?i)Sitemap:\s*(https?://\S+)", html):
                sm_html = fetch(sm_url.strip(), session)
                if sm_html:
                    for loc in re.findall(r"<loc>(.*?)</loc>", sm_html):
                        loc = loc.strip()
                        if any(kw in loc.lower() for kw in SITEMAP_KEYWORDS):
                            found.append(loc)
        if found:
            break
    result = []
    seen = set()
    for u in found:
        if u not in seen and domain in u:
            seen.add(u)
            result.append(u)
    return result[:10]


def try_wayback_machine(domain, session):
    emails = {}
    paths = ["/contact", "/contact-us", "/about", "/advertise"]
    for path in paths:
        url = "https://web.archive.org/web/2024/" + "https://www." + domain + path
        jitter()
        html = fetch(url, session)
        if html:
            for e in extract_emails(html):
                s = score_email(e)
                if s > -999:
                    emails[e] = max(emails.get(e, s), s)
    return emails


def try_hunter_io(domain):
    if not HUNTER_API_KEY:
        return {}
    emails = {}
    try:
        url = (
            "https://api.hunter.io/v2/domain-search"
            "?domain=" + domain +
            "&api_key=" + HUNTER_API_KEY +
            "&limit=10"
        )
        resp = requests.get(url, timeout=10, headers=make_headers())
        if resp.status_code == 200:
            data = resp.json()
            for entry in data.get("data", {}).get("emails", []):
                e = entry.get("value", "").lower()
                if e:
                    s = score_email(e)
                    if s > -999:
                        emails[e] = max(emails.get(e, s), s)
    except Exception:
        pass
    return emails


def try_google_search(domain):
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        return []
    urls = []
    try:
        query = quote_plus("site:" + domain + " contact OR email OR editorial OR advertise")
        url = (
            "https://www.googleapis.com/customsearch/v1"
            "?key=" + GOOGLE_API_KEY +
            "&cx=" + GOOGLE_CSE_ID +
            "&q=" + query +
            "&num=5"
        )
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            urls = [item.get("link", "") for item in data.get("items", [])]
    except Exception:
        pass
    return urls


def try_playwright(domain):
    if not ENABLE_PLAYWRIGHT or not HAS_PLAYWRIGHT:
        return {}
    emails = {}
    paths = ["/", "/contact", "/contact-us", "/about", "/advertise"]
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent=random.choice(USER_AGENTS), locale="en-GB")
            page = context.new_page()
            for path in paths:
                try:
                    url = "https://www." + domain + path
                    page.goto(url, timeout=15000, wait_until="networkidle")
                    time.sleep(1)
                    content = page.content()
                    for e in extract_emails(content):
                        s = score_email(e)
                        if s > -999:
                            emails[e] = max(emails.get(e, s), s)
                    if emails:
                        break
                except Exception:
                    pass
            browser.close()
    except Exception:
        pass
    return emails


def verify_email_smtp(email):
    if not ENABLE_SMTP_VERIFY or not HAS_DNS:
        return None
    try:
        domain = email.split("@")[1]
        mx_records = dns.resolver.resolve(domain, "MX", lifetime=5)
        mx_host = str(sorted(mx_records, key=lambda r: r.preference)[0].exchange).rstrip(".")
        with socket.create_connection((mx_host, 25), timeout=6) as sock:
            sock.recv(1024)
            sock.send(b"HELO outreach.check\r\n")
            sock.recv(1024)
            sock.send(b"MAIL FROM:<check@outreach.check>\r\n")
            sock.recv(1024)
            sock.send(("RCPT TO:<" + email + ">\r\n").encode())
            response = sock.recv(1024).decode(errors="ignore")
            sock.send(b"QUIT\r\n")
            if response.startswith("5"):
                return False
            return True
    except Exception:
        return None


def scrape_domain(domain):
    domain = re.sub(r"^https?://", "", domain.strip().lower())
    domain = re.sub(r"^www\.", "", domain).rstrip("/")
    base   = "https://www." + domain
    all_emails    = {}
    pages_checked = []
    source        = "scraper"
    checked       = set()

    def add_emails(text):
        for e in extract_emails(text):
            s = score_email(e)
            if s > -999:
                all_emails[e] = max(all_emails.get(e, s), s)

    def fetch_page(url, referer=None):
        if url in checked or len(pages_checked) >= MAX_PAGES:
            return None
        jitter()
        html = fetch(url, session, referer)
        if html:
            checked.add(url)
            pages_checked.append(url)
            add_emails(html)
        return html

    session = make_session()
    homepage_html = (
        fetch_page(base) or
        fetch_page("https://" + domain) or
        fetch_page("http://www." + domain)
    )
    if homepage_html:
        contact_links = find_contact_links(homepage_html, base)
    else:
        contact_links = []
    for path in CONTACT_PATHS:
        if len(pages_checked) >= MAX_PAGES: break
        fetch_page(base + path, referer=base)
    for url in contact_links:
        if len(pages_checked) >= MAX_PAGES: break
        fetch_page(url, referer=base)
    if len(all_emails) < 2:
        for url in get_sitemap_urls(domain, session):
            if len(pages_checked) >= MAX_PAGES: break
            fetch_page(url, referer=base)
    if not all_emails:
        logging.info("  Phase 2: Wayback Machine...")
        wb_emails = try_wayback_machine(domain, session)
        if wb_emails:
            all_emails.update(wb_emails)
            source = "wayback"
    if not all_emails and GOOGLE_API_KEY:
        logging.info("  Phase 2: Google Search...")
        for url in try_google_search(domain):
            if len(pages_checked) >= MAX_PAGES: break
            fetch_page(url, referer="https://www.google.com/")
        if all_emails:
            source = "google"
    if not all_emails and ENABLE_PLAYWRIGHT and HAS_PLAYWRIGHT:
        logging.info("  Phase 3: Playwright...")
        pw_emails = try_playwright(domain)
        if pw_emails:
            all_emails.update(pw_emails)
            source = "playwright"
    if not all_emails and HUNTER_API_KEY:
        logging.info("  Phase 4: Hunter.io...")
        hunter_emails = try_hunter_io(domain)
        if hunter_emails:
            all_emails.update(hunter_emails)
            source = "hunter"
    if all_emails and ENABLE_SMTP_VERIFY and HAS_DNS:
        for email, score in sorted(all_emails.items(), key=lambda x: x[1], reverse=True)[:5]:
            if verify_email_smtp(email) is False:
                logging.info("  SMTP rejected: " + email)
                all_emails[email] = -1
    ranked = [e for e, _ in sorted(all_emails.items(), key=lambda x: x[1], reverse=True) if all_emails[e] > 0]
    status = "error" if not pages_checked and not all_emails else ("no_email_found" if not ranked else "scraped")
    return {
        "domain": domain, "primary_email": ranked[0] if len(ranked) > 0 else "",
        "email_2": ranked[1] if len(ranked) > 1 else "",
        "email_3": ranked[2] if len(ranked) > 2 else "",
        "all_emails": " | ".join(ranked), "pages_checked": len(pages_checked),
        "source": source, "status": status, "date_scraped": datetime.now().strftime("%d/%m/%Y"),
    }


def load_domains(path):
    domains = []
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            for i, row in enumerate(csv.reader(f)):
                if not row: continue
                cell = row[0].strip()
                if i == 0 and cell.lower() in ("domain", "domains", "website", "url"): continue
                if cell: domains.append(cell)
    except FileNotFoundError:
        logging.error("Input file not found: " + path)
    return domains


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s", datefmt="%H:%M:%S")
    features = []
    if ENABLE_PLAYWRIGHT and HAS_PLAYWRIGHT: features.append("Playwright")
    elif ENABLE_PLAYWRIGHT and not HAS_PLAYWRIGHT: features.append("Playwright(unavailable)")
    if ENABLE_SMTP_VERIFY and HAS_DNS: features.append("SMTP-verify")
    elif ENABLE_SMTP_VERIFY and not HAS_DNS: features.append("SMTP-verify(dns-missing)")
    if HUNTER_API_KEY: features.append("Hunter.io")
    if GOOGLE_API_KEY: features.append("Google-Search")
    features += ["Cloudflare-decode", "Sitemap", "Wayback"]
    logging.info("v3.0 active features: " + ", ".join(features))
    domains = load_domains(INPUT_FILE)
    if not domains: logging.error("No domains. Exiting."); return
    logging.info("Loaded " + str(len(domains)) + " domains")
    fieldnames = ["domain", "primary_email", "email_2", "email_3",
                  "all_emails", "pages_checked", "source", "status", "date_scraped"]
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as out_f:
        writer = csv.DictWriter(out_f, fieldnames=fieldnames)
        writer.writeheader()
        for i, domain in enumerate(domains, 1):
            logging.info("[" + str(i) + "/" + str(len(domains)) + "] " + domain)
            try:
                result = scrape_domain(domain)
            except Exception as e:
                logging.warning("  Error: " + str(e))
                result = {"domain": domain, "primary_email": "", "email_2": "",
                          "email_3": "", "all_emails": "", "pages_checked": 0,
                          "source": "error", "status": "error",
                          "date_scraped": datetime.now().strftime("%d/%m/%Y")}
            writer.writerow(result)
            out_f.flush()
            msg = "  -> " + result["status"] + " [" + result["source"] + "]"
            if result["primary_email"]:
                msg += " | " + result["primary_email"]
                extras = [e for e in [result["email_2"], result["email_3"]] if e]
                if extras: msg += " | also: " + ", ".join(extras)
            logging.info(msg)
    logging.info("Done. Saved to " + OUTPUT_FILE)


if __name__ == "__main__":
    main()
