#!/usr/bin/env python3
"""
Email Scraper Agent v4.1
Architecture: HTTP Scraper -> Wayback CDX -> SMTP Pattern Verify
No Playwright. No Hunter.io. Free at any scale.
Multilingual contact-path coverage: 20+ languages.
"""

import csv
import os
import re
import smtplib
import time
from datetime import date
from urllib.parse import urljoin, urlparse

import dns.resolver
import requests
from bs4 import BeautifulSoup

# -- Constants ------------------------------------------------------------------

TIMEOUT = 15
MAX_PAGES_PER_DOMAIN = 50
OUTPUT_FILE = "emails_output.csv"
DOMAINS_FILE = "domains_input.csv"
WAYBACK_API = "http://web.archive.org/cdx/search/cdx"

CONTACT_PATHS = [
    "/contact", "/contact-us", "/contact_us", "/contactus",
    "/about", "/about-us", "/about_us", "/aboutus",
    "/advertise", "/advertising", "/advertise-with-us", "/advertise-here",
    "/editorial", "/editorial-team", "/editorial-policy",
    "/our-team", "/team", "/staff", "/masthead",
    "/partnerships", "/partner", "/partners",
    "/press", "/media", "/media-kit",
    "/write-for-us", "/contribute", "/submissions",
    "/work-with-us", "/collaborate",
]

MULTILINGUAL_PATHS = [
    # German (de, at, ch)
    "/kontakt", "/kontaktieren", "/kontakt-uns",
    "/uber-uns", "/ueber-uns", "/impressum",
    "/werben", "/werbung", "/mediadaten",
    "/redaktion", "/presse", "/medien",
    # French (fr, be, ch, ca)
    "/contactez-nous", "/nous-contacter",
    "/a-propos", "/qui-sommes-nous",
    "/publicite", "/annonceurs",
    "/redaction", "/equipe",
    "/partenaires", "/partenariat",
    # Spanish (es, mx, ar, co, cl, pe, etc.)
    "/contacto", "/contactenos", "/contactar",
    "/sobre-nosotros", "/quienes-somos", "/acerca-de",
    "/publicidad", "/anunciarse", "/anuncios",
    "/redaccion", "/equipo",
    "/prensa", "/medios", "/socios", "/colaborar",
    # Italian (it)
    "/contatti", "/contattaci",
    "/chi-siamo",
    "/pubblicita", "/inserzionisti",
    "/redazione", "/squadra",
    "/stampa",
    # Portuguese (pt, br)
    "/contato", "/fale-conosco",
    "/sobre-nos", "/quem-somos",
    "/publicidade", "/anuncie",
    "/redacao", "/imprensa", "/parceiros",
    # Dutch (nl, be)
    "/over-ons", "/neem-contact-op",
    "/adverteren", "/reclame",
    "/redactie", "/pers",
    # Swedish (se)
    "/kontakta-oss", "/om-oss",
    "/annonsera",
    # Norwegian (no)
    "/kontakt-oss",
    "/annonsere", "/redaksjonen",
    # Danish (dk)
    "/kontakt-os", "/om-os",
    "/annoncere",
    # Finnish (fi)
    "/yhteystiedot", "/ota-yhteytta",
    "/meista", "/mainonta", "/toimitus",
    # Polish (pl)
    "/o-nas", "/reklama", "/redakcja", "/prasa", "/partnerzy",
    # Russian (ru) -- romanised
    "/kontakty", "/o-kompanii", "/reklama", "/redaktsiya", "/press-tsentr",
    # Turkish (tr)
    "/iletisim", "/bize-ulasin",
    "/hakkimizda", "/kurumsal",
    "/reklam", "/reklam-ver",
    "/basin", "/medya", "/ortaklik",
    # Greek (gr) -- romanised
    "/epikoinonia", "/sxetika-me-mas",
    "/diafimisi", "/typos",
    # Czech (cz)
    "/kontaktujte-nas", "/o-nas",
    "/inzerce", "/redakce", "/tisk",
    # Slovak (sk)
    "/kontaktujte-nas",
    "/inzercia", "/redakcia",
    # Hungarian (hu)
    "/kapcsolat", "/rolunk",
    "/hirdetes", "/sajto",
    # Romanian (ro)
    "/contact", "/despre-noi",
    "/publicitate", "/presa", "/parteneri",
    # Bulgarian (bg) -- romanised
    "/kontakti", "/za-nas",
    "/reklama", "/medii",
    # Croatian (hr)
    "/kontakt", "/o-nama",
    "/oglasavanje", "/tisak",
    # Serbian (rs) -- romanised
    "/kontakt", "/o-nama",
    "/oglasavanje", "/mediji",
    # Ukrainian (ua) -- romanised
    "/kontakty", "/pro-nas",
    "/reklama", "/redaktsiya",
    # Catalan (es-cat)
    "/contacte", "/qui-som",
    "/publicitat", "/premsa",
    # Indonesian / Malay (id, my)
    "/hubungi-kami", "/tentang-kami",
    "/iklan", "/redaksi", "/pers",
    "/hubungi", "/mengenai-kami",
    "/pasang-iklan",
    # Vietnamese (vn) -- simplified
    "/lien-he", "/gioi-thieu",
    "/quang-cao", "/bao-chi",
    # Arabic -- romanised (ae, sa, eg, ma, etc.)
    "/ittasal-bina", "/ittisal",
    "/hawlana", "/man-nahnu",
    "/ilaan", "/wasail-ilam",
    # Hebrew -- romanised (il)
    "/tzor-kesher", "/anachnu",
    "/prsume",
    # Japanese -- romanised (jp)
    "/toiawase", "/otoiawase",
    "/kaisha-annai", "/koukoku",
    # Korean -- romanised (kr)
    "/munuihada", "/hoesa-sogae",
    "/gwanggo", "/eon-ron",
    # Chinese -- romanised (cn, tw, hk)
    "/lianxi-women", "/guanyu-women",
    "/guanggao", "/xinwen",
    # Welsh (uk-wales)
    "/cysylltu", "/amdanom-ni",
    "/hysbysebu",
    # Latvian (lv)
    "/kontakti", "/par-mums",
    "/reklama", "/prese",
    # Lithuanian (lt)
    "/kontaktai", "/apie-mus",
    "/reklama", "/spauda",
    # Estonian (ee)
    "/kontakt", "/meist",
    "/reklaam", "/ajakirjandus",
    # Slovenian (si) -- ASCII only
    "/kontakt", "/o-nas",
    "/oglasevanje", "/tisk",
    # Albanian (al)
    "/kontakt", "/rreth-nesh",
    "/reklamim", "/shtyp",
]

EMAIL_SCORES = {
    "editor": 100, "editorial": 100,
    "partnerships": 100, "partnership": 100,
    "advertising": 100, "advertise": 100,
    "press": 95, "media": 95,
    "news": 90, "content": 85,
    "contact": 60, "admin": 60,
    "hello": 55, "team": 55,
    "info": 30, "mail": 20,
    "web": 20, "support": 15,
}

EMAIL_REGEX = re.compile(
    r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b'
)

SKIP_PATTERN = re.compile(
    r'(noreply|no-reply|donotreply|unsubscribe|bounce|spam|test@|'
    r'\d+x\d+|@2x\.\.png|\.jpg|\.jpeg|\.gif|\.svg|\.webp|\.ico|'
    r'example\.com|sentry\.|wixpress\.com)',
    re.IGNORECASE,
)

BAD_TLDS = {"png", "jpg", "jpeg", "gif", "svg", "webp", "ico", "css", "js", "xml"}

SMTP_PATTERNS = [
    "editor", "editorial", "advertising", "advertise",
    "partnerships", "press", "media", "contact",
    "news", "content", "hello", "info",
]

FIELDNAMES = [
    "domain", "primary_email", "email_2", "email_3", "all_emails",
    "pages_checked", "source", "status",
    "contact_form", "contact_form_url",
    "wayback_snapshot_date", "date_scraped",
]

# -- HTTP helpers ---------------------------------------------------------------

def make_session():
    s = requests.Session()
    s.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    })
    return s


def fetch(url, session, referer=None):
    """Fetch a URL and return HTML text, or None on failure."""
    try:
        headers = {}
        if referer:
            headers["Referer"] = referer
        resp = session.get(
            url,
            timeout=TIMEOUT,
            headers=headers,
            allow_redirects=True,
        )
        if resp.status_code == 200:
            return resp.text
        return None
    except Exception:
        return None

# -- Email extraction ----------------------------------------------------------

def decode_cloudflare_email(encoded):
    """Decode a Cloudflare data-cfemail encoded string."""
    try:
        key = int(encoded[:2], 16)
        return "".join(
            chr(int(encoded[i:i + 2], 16) ^ key)
            for i in range(2, len(encoded), 2)
        )
    except Exception:
        return ""


def extract_emails(html, domain):
    """
    Extract emails from HTML. Returns list of (email, score) sorted by score desc.
    Decodes Cloudflare obfuscation, checks mailto: links, filters false positives.
    """
    if not html:
        return []

    soup = BeautifulSoup(html, "lxml")

    for el in soup.find_all(attrs={"data-cfemail": True}):
        decoded = decode_cloudflare_email(el.get("data-cfemail", ""))
        if decoded:
            el.string = decoded

    text = soup.get_text(separator=" ")

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.lower().startswith("mailto:"):
            email_part = href[7:].split("?")[0].strip()
            text += " " + email_part

    raw_emails = EMAIL_REGEX.findall(text)

    seen = {}
    for email in raw_emails:
        email = email.lower().strip(".")
        if email in seen:
            continue
        if SKIP_PATTERN.search(email):
            continue
        tld = email.rsplit(".", 1)[-1]
        if tld in BAD_TLDS:
            continue
        local = email.split("@")[0]
        score = 0
        for keyword, s in EMAIL_SCORES.items():
            if keyword in local:
                score = max(score, s)
        if score == 0:
            score = 10
        seen[email] = score

    return sorted(seen.items(), key=lambda x: -x[1])

# -- Contact form detection ----------------------------------------------------

def detect_contact_form(html, page_url):
    if not html:
        return False, None
    soup = BeautifulSoup(html, "lxml")
    for form in soup.find_all("form"):
        inputs = form.find_all(["input", "textarea"])
        relevant = [
            i for i in inputs
            if i.get("type", "text").lower() in ("text", "email", "textarea", "")
            or i.name == "textarea"
        ]
        if len(relevant) >= 2:
            return True, page_url
    return False, None

# -- Phase 1: HTTP scraper -----------------------------------------------------

def phase1_http(domain, session):
    base_url = "https://" + domain
    checked_urls = set()
    all_emails = {}
    pages_checked = 0
    contact_form = ""
    contact_form_url = ""

    def try_fetch(url):
        nonlocal pages_checked
        if url in checked_urls:
            return None
        checked_urls.add(url)
        pages_checked += 1
        return fetch(url, session, referer=base_url)

    def absorb(html, page_url):
        nonlocal contact_form, contact_form_url
        if not html:
            return
        emails = extract_emails(html, domain)
        for email, score in emails:
            if email not in all_emails or score > all_emails[email]:
                all_emails[email] = score
        if not contact_form:
            found, furl = detect_contact_form(html, page_url)
            if found:
                contact_form = "Yes"
                contact_form_url = furl

    # Sitemap
    sitemap_hits = []
    for sm_path in ["/sitemap.xml", "/sitemap_index.xml", "/sitemap-index.xml"]:
        sm_html = try_fetch(base_url + sm_path)
        if sm_html:
            soup = BeautifulSoup(sm_html, "lxml-xml")
            locs = [loc.text.strip() for loc in soup.find_all("loc")]
            kws = {"contact", "about", "advertise", "editorial", "team", "press", "partner", "staff"}
            hits = [l for l in locs if any(kw in l.lower() for kw in kws)]
            sitemap_hits.extend(hits[:6])
            if locs:
                break

    # Homepage
    hp_html = try_fetch(base_url)
    absorb(hp_html, base_url)

    # Sitemap hits -> English paths -> multilingual paths, deduplicated
    seen_paths = set()
    priority_urls = []
    for p in sitemap_hits + [base_url + p for p in CONTACT_PATHS + MULTILINGUAL_PATHS]:
        if p not in seen_paths:
            seen_paths.add(p)
            priority_urls.append(p)

    for url in priority_urls:
        if pages_checked >= MAX_PAGES_PER_DOMAIN:
            break
        html = try_fetch(url)
        absorb(html, url)

    emails_sorted = sorted(all_emails.items(), key=lambda x: -x[1])
    return {
        "emails": emails_sorted,
        "pages_checked": pages_checked,
        "contact_form": contact_form,
        "contact_form_url": contact_form_url,
    }

# -- Phase 2: Wayback Machine --------------------------------------------------

def phase2_wayback(domain, session):
    all_emails = {}
    pages_checked = 0
    snapshot_date = ""
    contact_form = ""
    contact_form_url = ""
    cdx_results = []

    kw_queries = ["contact", "about", "advertise", "editorial", "press"]
    for kw in kw_queries[:4]:
        try:
            params = {
                "url": domain + "/*" + kw + "*",
                "output": "json",
                "fl": "original,timestamp",
                "filter": "statuscode:200",
                "limit": "3",
                "collapse": "urlkey",
            }
            resp = session.get(WAYBACK_API, params=params, timeout=TIMEOUT)
            if resp.status_code == 200:
                data = resp.json()
                for row in data[1:]:
                    cdx_results.append((row[0], row[1]))
        except Exception:
            pass

    try:
        params = {
            "url": domain,
            "output": "json",
            "fl": "original,timestamp",
            "filter": "statuscode:200",
            "limit": "2",
            "collapse": "urlkey",
        }
        resp = session.get(WAYBACK_API, params=params, timeout=TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            for row in data[1:]:
                cdx_results.append((row[0], row[1]))
    except Exception:
        pass

    seen_orig = set()
    for orig_url, timestamp in cdx_results[:8]:
        if orig_url in seen_orig:
            continue
        seen_orig.add(orig_url)
        wayback_url = "https://web.archive.org/web/" + timestamp + "/" + orig_url
        html = fetch(wayback_url, session)
        pages_checked += 1
        if html:
            if not snapshot_date and len(timestamp) >= 8:
                ts = timestamp[:8]
                snapshot_date = ts[:4] + "-" + ts[4:6] + "-" + ts[6:8]
            emails = extract_emails(html, domain)
            for email, score in emails:
                if email not in all_emails or score > all_emails[email]:
                    all_emails[email] = score
            if not contact_form:
                found, _ = detect_contact_form(html, orig_url)
                if found:
                    contact_form = "Unsure"
                    contact_form_url = orig_url

    emails_sorted = sorted(all_emails.items(), key=lambda x: -x[1])
    return {
        "emails": emails_sorted,
        "pages_checked": pages_checked,
        "snapshot_date": snapshot_date,
        "contact_form": contact_form,
        "contact_form_url": contact_form_url,
    }

# -- Phase 3: SMTP pattern verify ----------------------------------------------

def phase3_smtp(domain):
    try:
        mx_records = dns.resolver.resolve(domain, "MX")
        mx_host = str(
            sorted(mx_records, key=lambda r: r.preference)[0].exchange
        ).rstrip(".")
    except Exception:
        return []

    verified = []
    for pattern in SMTP_PATTERNS:
        email = pattern + "@" + domain
        try:
            with smtplib.SMTP(timeout=10) as smtp:
                smtp.connect(mx_host, 25)
                smtp.helo("linkjuiceclub.com")
                smtp.mail("verify@linkjuiceclub.com")
                code, _ = smtp.rcpt(email)
                if code == 250:
                    score = EMAIL_SCORES.get(pattern, 10)
                    verified.append((email, score))
                smtp.quit()
        except Exception:
            pass
        time.sleep(0.3)

    return sorted(verified, key=lambda x: -x[1])

# -- Row builder ---------------------------------------------------------------

def build_row(domain, email_list, pages_checked, source,
              contact_form, contact_form_url, wayback_snapshot_date):
    emails = [e for e, _ in email_list]
    status = "scraped" if emails else "no_email_found"
    return {
        "domain": domain,
        "primary_email": emails[0] if len(emails) > 0 else "",
        "email_2":       emails[1] if len(emails) > 1 else "",
        "email_3":       emails[2] if len(emails) > 2 else "",
        "all_emails":    " | ".join(emails),
        "pages_checked": pages_checked,
        "source":        source,
        "status":        status,
        "contact_form":  contact_form,
        "contact_form_url": contact_form_url,
        "wayback_snapshot_date": wayback_snapshot_date,
        "date_scraped":  date.today().strftime("%d/%m/%Y"),
    }


def error_row(domain):
    return {
        "domain": domain,
        "primary_email": "", "email_2": "", "email_3": "", "all_emails": "",
        "pages_checked": 0, "source": "", "status": "error",
        "contact_form": "", "contact_form_url": "",
        "wayback_snapshot_date": "", "date_scraped": date.today().strftime("%d/%m/%Y"),
    }

# -- Domain orchestrator -------------------------------------------------------

def scrape_domain(domain, session):
    contact_form = ""
    contact_form_url = ""
    wayback_snapshot_date = ""
    total_pages = 0

    print("[" + domain + "] Phase 1: HTTP scraper...")
    p1 = phase1_http(domain, session)
    total_pages += p1["pages_checked"]

    if p1["contact_form"]:
        contact_form = p1["contact_form"]
        contact_form_url = p1["contact_form_url"]

    if p1["emails"]:
        print("[" + domain + "] Phase 1 found " + str(len(p1["emails"])) + " emails.")
        return build_row(domain, p1["emails"], total_pages, "scraper",
                         contact_form, contact_form_url, "")

    print("[" + domain + "] Phase 2: Wayback Machine...")
    p2 = phase2_wayback(domain, session)
    total_pages += p2["pages_checked"]
    wayback_snapshot_date = p2["snapshot_date"]

    if p2["contact_form"] and not contact_form:
        contact_form = p2["contact_form"]
        contact_form_url = p2["contact_form_url"]

    if p2["emails"]:
        print("[" + domain + "] Phase 2 found " + str(len(p2["emails"])) + " emails.")
        return build_row(domain, p2["emails"], total_pages, "wayback_unsure",
                         contact_form, contact_form_url, wayback_snapshot_date)

    enable_smtp = os.environ.get("ENABLE_SMTP_VERIFY", "false").lower() == "true"
    if enable_smtp:
        print("[" + domain + "] Phase 3: SMTP pattern verify...")
        p3 = phase3_smtp(domain)
        if p3:
            print("[" + domain + "] Phase 3 verified " + str(len(p3)) + " emails.")
            return build_row(domain, p3, total_pages, "smtp_verified",
                             contact_form, contact_form_url, wayback_snapshot_date)

    print("[" + domain + "] No emails found.")
    row = build_row(domain, [], total_pages, "", contact_form, contact_form_url, wayback_snapshot_date)
    row["status"] = "no_email_found"
    return row

# -- Entry point ---------------------------------------------------------------

def load_domains():
    if not os.path.exists(DOMAINS_FILE):
        print("ERROR: " + DOMAINS_FILE + " not found.")
        return []
    with open(DOMAINS_FILE, encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)
    if rows and rows[0] and rows[0][0].strip().lower() == "domain":
        rows = rows[1:]
    return [row[0].strip() for row in rows if row and row[0].strip()]


def normalise(domain):
    domain = domain.strip().lower()
    for prefix in ("https://www.", "http://www.", "https://", "http://"):
        if domain.startswith(prefix):
            domain = domain[len(prefix):]
    return domain.rstrip("/")


def main():
    domains = load_domains()
    if not domains:
        print("No domains to process. Add them to " + DOMAINS_FILE)
        return

    print("Starting scraper -- " + str(len(domains)) + " domains.")
    session = make_session()

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()

        for idx, raw_domain in enumerate(domains, 1):
            domain = normalise(raw_domain)
            print("\n[" + str(idx) + "/" + str(len(domains)) + "] " + domain)
            try:
                row = scrape_domain(domain, session)
                writer.writerow(row)
                f.flush()
            except Exception as exc:
                print("[" + domain + "] Fatal: " + str(exc))
                writer.writerow(error_row(domain))
                f.flush()

            time.sleep(1)

    print("\nDone. Results saved to " + OUTPUT_FILE)


if __name__ == "__main__":
    main()
