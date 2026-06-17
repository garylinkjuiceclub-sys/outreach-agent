#!/usr/bin/env python3
"""
Email Scraper Agent v4.9
Architecture: Phase0 Relevance Filter -> HTTP Scraper -> Wayback CDX -> SMTP Pattern Verify
No Playwright. No Hunter.io. Free at any scale.
Multilingual contact-path coverage: 30+ languages.

v4.9 changes (per-domain time bounds — fixes large batches STILL hitting 6h):
- Run #24 (v4.8) processed only 732/874 domains in 6h (~5 min/domain). Root
  cause: Phase 1 tried up to 50 pages at a 15s timeout against slow/dead
  foreign sites — up to ~12 min wasted on a single hanging domain. Concurrency
  alone could not outrun that.
- MAX_PAGES_PER_DOMAIN 50 -> 12; TIMEOUT 15s -> 8s.
- HARD PER-DOMAIN BUDGETS: Phase 1 capped at PHASE1_BUDGET_SEC, Phase 2 at
  PHASE2_BUDGET_SEC, checked inside the fetch loops so one slow site can't tie
  up a worker for minutes. Wayback archive fetches 8 -> 4, CDX retries 3 -> 2.
- Default MAX_WORKERS 10 -> 16.

v4.8 changes (throughput overhaul — large batches no longer hit the 6h cap):
- DOMAIN-LEVEL CONCURRENCY: domains are now scraped in parallel via a
  ThreadPoolExecutor (default 10 workers, override with MAX_WORKERS env var).
  Each domain still scrapes its own pages sequentially, so per-domain results
  are byte-for-byte identical to v4.7 — only the wall-clock time changes.
  Each worker uses its own requests.Session; output is written under a lock
  and flushed per row (resilient to mid-run termination). NOTE: output rows are
  now in completion order, not input order (every row is still labelled by
  domain). verified/needs_manual_check classification is unchanged.
- SMTP FAIL-FAST + CONNECTION REUSE: phase3_smtp now opens ONE connection
  (connect/HELO/MAIL once) and reuses it for the catch-all probe and all
  pattern RCPTs, instead of reconnecting 13 times. If the MX cannot be reached
  at all (e.g. port 25 blocked), it returns immediately instead of looping
  every pattern against a dead socket. SMTP timeout lowered 10s -> 7s.
  SMTP results are still deliverable GUESSES -> always needs_manual_check.
- Wayback CDX queries gained light retry/backoff to protect Phase 2 recall
  when many workers hit web.archive.org at once.

v4.7 changes (reliability overhaul):
- STRICT VERIFICATION: only emails found on the LIVE site whose domain matches
  the site domain get status=verified / confidence=high.
  Everything else (Wayback, SMTP guesses, off-domain emails) is recorded but
  gets status=needs_manual_check + review_flag=yes + review_reason.
- email_source_url column: the exact page where the primary email was found,
  so the team can verify any email in one click.
- review_reason column: why a row needs manual review
  (wayback_archive / smtp_guess / smtp_catchall / domain_mismatch /
   unclassified_niche / no_email_found).
- Obfuscated-email decoding: "info [at] domain [dot] com" patterns.
- Phase 0 relevance filter now scans title/meta/og/h1/h2 (strong zone) PLUS
  nav/footer links and body text (weak zone, needs 2+ keyword hits to block,
  to avoid false positives). Sites whose title/meta positively identify them
  as content sites are never weak-zone blocked.
- New blocklist categories: Invoicing / Payroll, Forums, Visiting Places /
  Attractions, Local Events. Expanded keywords across existing categories.
- Domains that match no positive content niche ("General / Other") are still
  scraped but review_flag=yes (review_reason=unclassified_niche).
"""

import concurrent.futures
import csv
import json
import os
import re
import smtplib
import threading
import time
from datetime import date
from urllib.parse import urljoin, urlparse

import dns.resolver
import requests
from bs4 import BeautifulSoup

# -- Constants ------------------------------------------------------------------

TIMEOUT = 8              # v4.9: was 15; dead/slow pages fail ~2x faster
SMTP_TIMEOUT = 7          # v4.8: was 10; conservative enough for slow MX servers
MAX_PAGES_PER_DOMAIN = 12   # v4.9: was 50 — contact info lives on the first few pages
# v4.9: hard per-domain time budgets so one slow/hanging site can't tie up a
# worker for minutes. Checked inside the Phase 1 and Phase 2 fetch loops.
PHASE1_BUDGET_SEC = 45
PHASE2_BUDGET_SEC = 35
# v4.8: domains scraped in parallel; v4.9 default raised 10 -> 16.
# Override with the MAX_WORKERS env var.
MAX_WORKERS = int(os.environ.get("MAX_WORKERS", "16"))
OUTPUT_FILE = "emails_output.csv"
DOMAINS_FILE = "domains_input.csv"
WAYBACK_API = "http://web.archive.org/cdx/search/cdx"

# Weak-zone (nav/footer/body) blocklist matches need this many DISTINCT
# keyword hits in the same category before a domain is skipped.
WEAK_BLOCK_MIN_HITS = 2

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

# Obfuscated email patterns: "info [at] domain [dot] com", "info (at) domain.com"
OBFUSCATED_AT = re.compile(r'\s*[\[\(\{]\s*(?:at|@)\s*[\]\)\}]\s*', re.IGNORECASE)
OBFUSCATED_DOT = re.compile(r'\s*[\[\(\{]\s*(?:dot)\s*[\]\)\}]\s*', re.IGNORECASE)

SKIP_PATTERN = re.compile(
    r'(noreply|no-reply|donotreply|unsubscribe|bounce|spam|test@|'
    r'\d+x\d+|@2x\.|\.png|\.jpg|\.jpeg|\.gif|\.svg|\.webp|\.ico|'
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
    "email_source_url",
    "pages_checked", "source", "status", "niche",
    "confidence", "review_flag", "review_reason",
    "contact_form", "contact_form_url",
    "wayback_snapshot_date", "date_scraped",
]

# Second-level public suffixes for registrable-domain comparison.
SECOND_LEVEL_TLDS = {
    "co", "com", "org", "net", "ac", "gov", "edu", "or", "ne", "go",
}

# Niche blocklist — organised by category.
# phase0_relevance() checks two zones:
#   STRONG zone (title, meta description/keywords, og:* tags, h1/h2):
#     a single keyword match blocks the domain.
#   WEAK zone (nav/footer link text, first 4000 chars of body text):
#     needs WEAK_BLOCK_MIN_HITS distinct keyword matches in the same
#     category to block (avoids false positives from passing mentions).
# Skipped domains appear in CSV as status=skipped_irrelevant, niche=<Category>.
# Add/remove keywords here to tune the filter.
SKIP_NICHE_CATEGORIES = {
    "Education": [
        "primary school", "secondary school", "elementary school", "middle school",
        "high school", "kindergarten", "preschool", "nursery school", "infant school",
        "junior school", "boarding school", "grammar school",
    ],
    "Government": [
        "government website", "official government", "city council", "town council",
        "county council", "borough council", "district council", "parish council",
        "town hall", "city hall", "ministry of", "department of", "municipal website",
    ],
    "Health / Medical": [
        # Hospitals & broad health
        "hospital", "nhs trust", "medical center", "medical centre",
        "health centre", "health center", "healthcare provider",
        "medical practice", "family medicine", "family health",
        "women's health", "men's health",
        # Clinics
        "clinic",
        # Dental
        "dental", "dentist", "dentistry", "dental surgery", "dental practice",
        # Doctors & physicians
        "doctor", "physician", "gp surgery",
        "surgeon", "orthopedic", "orthopaedic", "m.d.", ", md",
        # Hearing / audiology (v4.7 — caught appliedhearingaz.com-style sites)
        "hearing aid", "hearing aids", "audiology", "audiologist", "hearing care",
        "hearing test",
        # Fertility / reproductive (v4.7 — caught cryobankamerica.com-style sites)
        "fertility", "sperm bank", "cryobank", "ivf", "women's clinic",
        "womens clinic",
        # Patient-facing signals (v4.7)
        "patient portal", "telehealth", "primary care", "book an appointment",
        "request an appointment",
        # Therapy
        "physical therapy", "physiotherapy", "physiotherapy clinic",
        "occupational therapy", "speech therapy",
        # Mental health
        "psychologist", "psychological", "psychology", "psychiatry", "psychiatrist",
        "mental health clinic", "counselling centre", "counseling center",
        # Specialties
        "pediatrics", "pediatric", "paediatrics", "paediatric",
        "radiology", "radiologist",
        "optometry", "optometrist",
        "chiropractic", "chiropractor",
        "allergy clinic", "allergist",
        "urgent care",
        # Rehab / addiction
        "rehabilitation center", "rehabilitation centre",
        "rehab center", "rehab centre",
        "addiction treatment", "recovery center", "recovery centre",
        "detox center", "detox centre",
        # Pharma (v4.7 — caught jynneos.com-style drug/vaccine sites)
        "pharmaceutical", "pharma", "vaccine", "prescribing information",
        "prescription medicine", "fda approved", "side effects",
    ],
    "Community / Municipality": [
        "community centre", "community center", "local authority",
    ],
    "Funeral Services": [
        "funeral home", "funeral director", "funeral services", "crematorium",
        "burial services", "memorial chapel", "cremation services",
    ],
    "Restaurants / Food": [
        "restaurant", "takeaway", "fast food", "pizza delivery",
        "book a table", "reserve a table", "our menu", "order online",
        "lunch menu", "dinner menu", "brunch menu",
    ],
    "E-commerce / Online Shops": [
        "add to cart", "add to basket", "shopping cart", "online shop", "online store",
        # v4.7 — caught shopjayne.com / cozyproducts.com-style storefronts
        "shop now", "free shipping", "add to bag", "buy now",
        "powered by shopify", "your cart", "view cart",
        "best sellers", "new arrivals", "shop all", "free returns",
        "checkout",
    ],
    "Telephone / ISP": [
        "mobile network", "mobile operator", "broadband provider",
        "internet service provider", "sim only", "phone contract",
    ],
    "Religion": [
        "church of", "parish church", "roman catholic", "mosque", "synagogue",
        "buddhist temple", "hindu temple", "diocese", "place of worship",
    ],
    "Politics": [
        "political party", "member of parliament", "election campaign",
        "constituency", "senator for",
    ],
    "Research / Academia": [
        "research institute", "research center", "research centre",
        "think tank", "academic journal",
    ],
    "Forums": [
        "discussion forum", "community forum", "message board",
        "discussion board", "phpbb", "vbulletin", "forum index",
    ],
    "Public Transport": [
        "bus timetable", "train timetable", "public transport", "transit authority",
    ],
    "Weather": [
        "weather forecast", "weather service", "meteorological office",
    ],
    "Invoicing / Payroll": [
        "invoicing software", "invoice generator", "invoicing",
        "payroll", "payroll services", "payroll software",
        "bookkeeping services", "accounting software",
    ],
    "Gardening": [
        "garden centre", "garden center", "plant nursery", "gardening supplies",
    ],
    "Construction / Trades": [
        "building contractor", "construction company", "roofing contractor",
        "plumbing company", "electrical contractor",
        "restoration contractor", "restoration services",
        "exterior contractor", "siding contractor",
        "hvac contractor", "hvac company",
        # v4.7 — caught penguinair.com / plateauexcavation.com-style sites
        "hvac", "air conditioning", "heating and cooling", "heating & cooling",
        "garage door", "garage doors", "excavation",
        "plumbing services", "roofing services", "general contractor",
        "pest control",
    ],
    "Hair / Beauty": [
        "hair salon", "hair & beauty", "hairdresser", "barbershop", "barber shop",
        "beauty salon", "nail salon", "tanning salon",
        "hair studio", "beauty studio", "day spa",
    ],
    "Law / Legal": [
        "law firm", "solicitors", "barristers", "attorneys at law",
        "legal services", "law office",
        "attorney", "attorneys", "personal injury lawyer",
        "criminal defense", "criminal defence",
        "family law", "immigration lawyer",
    ],
    "Flight Booking": [
        "ryanair", "wizzair", "wizz air", "easyjet", "kiwi.com",
        "flight booking", "book flights", "cheap flights",
    ],
    "Storage": [
        "self storage", "self-storage", "storage units", "storage facility",
    ],
    "Hotels / Accommodation": [
        "hotel", "motel", "bed and breakfast", "book a room", "hostel",
        "resort", "boutique hotel", "luxury resort",
        "book your stay", "check-in date", "room rates",
    ],
    "Children's Entertainment": [
        "children's entertainment", "kids entertainment", "amusement park",
        "soft play", "play centre", "play center",
    ],
    "Security": [
        "security company", "security guard", "cctv installation",
        "alarm installation", "private security",
    ],
    "Museums / Culture": [
        "museum", "art gallery", "heritage site",
    ],
    "Visiting Places / Attractions": [
        "tourist attraction", "visitor attraction", "plan your visit",
        "things to do in", "visitor centre", "visitor center",
        "opening times", "buy tickets",
    ],
    "Local Events": [
        "upcoming events", "events calendar", "event calendar",
        "event tickets", "what's on", "whats on",
    ],
    "Gyms / Fitness": [
        "fitness centre", "fitness center", "health club", "gym membership",
        "yoga studio", "pilates studio",
    ],
    "Job Portals": [
        "job portal", "job board", "find jobs", "job listings",
        "recruitment agency", "staffing agency",
        "care careers", "healthcare careers", "healthcare jobs",
        "nursing careers", "nursing jobs", "care jobs",
        "jobs in care", "jobs in healthcare", "apply for jobs",
        "browse jobs", "search jobs", "submit your cv",
    ],
    "Cannabis / Dispensary": [
        "cannabis", "marijuana", "dispensary", "cannabis dispensary",
        "cannabis farm", "cannabis delivery", "weed delivery",
        "thc", "cbd", "cbd shop", "cbd store", "cbd products",
        "hemp farm", "hemp products", "cannabis club",
        "medical marijuana", "recreational cannabis",
        "pot shop", "cannabis retail",
    ],
    "Insurance": [
        "insurance company", "insurance broker", "insurance quote",
        "insurance provider",
    ],
    "Pharmacy": [
        "pharmacy", "pharmacist", "chemist", "drugstore",
    ],
    "University": [
        "university", "higher education", "undergraduate courses",
        "postgraduate", "student union",
    ],
    "Police / Law Enforcement": [
        "police service", "police force", "law enforcement",
        "constabulary", "police department",
    ],
    "Festival": [
        "music festival", "arts festival", "cultural festival",
        "festival lineup", "festival tickets",
    ],
    "Zoo / Wildlife": [
        "zoo", "wildlife park", "aquarium", "safari park", "zoological",
    ],
    "Events / Venues": [
        "event venue", "conference centre", "conference center",
        "convention centre", "exhibition centre",
    ],
    "Artists / Shows": [
        "official artist", "tour dates", "concert tickets", "discography",
    ],
    "Shopping Mall": [
        "shopping centre", "shopping center", "shopping mall",
        "retail park", "outlet mall",
    ],
    "Bar / Pub": [
        "nightclub", "cocktail bar", "taproom", "gastropub", "craft brewery",
        " pub", "pub ", "bar & grill", "bar and grill", "cabaret",
        "happy hour", "live music venue",
    ],
}

# Positive niche classifier — applied to domains that PASS the blocklist.
# Checks the same homepage HTML already fetched in phase0 (no extra requests).
# Strong-zone hits count double; the highest-scoring category wins.
# If nothing matches, falls back to "General / Other" AND the row is
# review-flagged (unclassified_niche) so the team checks relevance manually.
NICHE_CATEGORIES = {
    "Blog / Content Site": [
        "blog", "our blog", "latest posts", "content creator", "blogger",
        "read our posts", "written by", "authored by",
    ],
    "News / Media": [
        "breaking news", "latest news", "news and updates", "newsroom",
        "editorial", "journalist", "publication", "media outlet",
        "press release", "reporter",
    ],
    "Magazine": [
        "magazine", "digital magazine", "online magazine",
        "subscribe to our magazine", "latest issue",
    ],
    "Review Site": [
        "review", "reviews", "best of", "top 10", "buying guide",
        "comparison", "rated", "our verdict", "pros and cons",
    ],
    "Technology": [
        "tech blog", "technology blog", "software", "startup",
        "developer blog", "tech news", "saas", "app review",
    ],
    "Finance / Business": [
        "finance", "business news", "personal finance", "investing",
        "money tips", "entrepreneur", "financial tips",
    ],
    "Travel": [
        "travel blog", "travel guide", "travel tips", "destination",
        "wanderlust", "travel and adventure",
    ],
    "Food & Drink": [
        "food blog", "recipes", "cooking tips", "culinary",
        "food and drink", "foodie", "recipe",
    ],
    "Health & Wellness": [
        "wellness blog", "healthy living", "nutrition tips", "fitness tips",
        "health blog", "wellbeing", "mindfulness",
    ],
    "Lifestyle": [
        "lifestyle blog", "fashion", "style guide", "home decor",
        "living tips", "life tips", "parenting",
    ],
    "Sports": [
        "sports blog", "sports news", "match report", "athletics",
        "football blog", "sports tips",
    ],
    "Entertainment": [
        "entertainment", "celebrity news", "movies", "tv shows",
        "pop culture", "film review",
    ],
    "Education / Resources": [
        "how-to guide", "tutorial", "tips and tricks",
        "online course", "learning resources", "free guide",
    ],
    "Pets": [
        "pet blog", "dog blog", "cat blog", "pet care tips",
        "animal lover", "pet owner",
    ],
    "Environment / Green": [
        "sustainability", "eco-friendly", "green living",
        "environment blog", "climate", "zero waste",
    ],
}

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

# -- Domain matching -------------------------------------------------------------

def registrable_domain(host):
    """Best-effort registrable domain: example.com, example.co.uk."""
    parts = host.lower().strip(".").split(".")
    if len(parts) >= 3 and parts[-2] in SECOND_LEVEL_TLDS:
        return ".".join(parts[-3:])
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return host.lower()


def email_matches_domain(email, domain):
    """True if the email's domain belongs to the same site as `domain`."""
    if "@" not in email:
        return False
    email_dom = email.rsplit("@", 1)[1].lower()
    site_dom = domain.lower()
    if email_dom == site_dom:
        return True
    if email_dom.endswith("." + site_dom) or site_dom.endswith("." + email_dom):
        return True
    return registrable_domain(email_dom) == registrable_domain(site_dom)

# -- Phase 0: Relevance filter -------------------------------------------------

def phase0_relevance(domain, session):
    """
    Quick pre-scrape check using only the homepage (one HTTP request).

    Two signal zones:
      STRONG: title, meta description/keywords, og:* tags, first 8 h1/h2 —
              one blocklist keyword match here skips the domain.
      WEAK:   nav/footer link text + first 4000 chars of visible body text —
              needs WEAK_BLOCK_MIN_HITS distinct keyword matches in the same
              category to skip (avoids blocking a blog that merely mentions
              a hotel once).

    A domain whose STRONG zone positively identifies it as a content site
    (NICHE_CATEGORIES match in title/meta/h1) is never weak-zone blocked.

    Returns (relevant, matched_kw, skip_category, detected_niche).
      - Blocked:  (False, matched_keyword(s), skip_category, "")
      - Passing:  (True,  "", "", detected_niche)   # may be "General / Other"
      - On connection failure: (True, "", "", "") so phase1 can try properly.
    """
    base_url = "https://" + domain
    try:
        resp = session.get(base_url, timeout=8, allow_redirects=True)
        html = resp.text if resp.status_code == 200 else None
    except Exception:
        return True, "", "", ""

    if not html:
        return True, "", "", ""

    soup = BeautifulSoup(html, "lxml")

    # --- STRONG zone ---
    strong_parts = []
    if soup.title and soup.title.string:
        strong_parts.append(soup.title.string)
    for name in ("description", "keywords"):
        tag = soup.find("meta", attrs={"name": name})
        if tag and tag.get("content"):
            strong_parts.append(tag["content"])
    for prop in ("og:title", "og:description", "og:site_name", "og:type"):
        tag = soup.find("meta", attrs={"property": prop})
        if tag and tag.get("content"):
            strong_parts.append(tag["content"])
    for h in soup.find_all(["h1", "h2"])[:8]:
        strong_parts.append(h.get_text(" "))
    strong_text = " ".join(strong_parts).lower()

    # --- WEAK zone ---
    weak_parts = []
    for container in soup.find_all(["nav", "footer"]):
        for a in container.find_all("a"):
            weak_parts.append(a.get_text(" "))
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    weak_parts.append(soup.get_text(" ")[:4000])
    weak_text = " ".join(weak_parts).lower()

    # 1. Strong-zone blocklist: single hit blocks.
    for category, keywords in SKIP_NICHE_CATEGORIES.items():
        for kw in keywords:
            if kw.lower() in strong_text:
                return False, kw.strip(), category, ""

    # 2. Strong-zone positive ID: trusted, skip weak-zone blocking.
    strong_positive = ""
    for category, keywords in NICHE_CATEGORIES.items():
        for kw in keywords:
            if kw.lower() in strong_text:
                strong_positive = category
                break
        if strong_positive:
            break
    if strong_positive:
        return True, "", "", strong_positive

    # 3. Weak-zone blocklist: needs >= WEAK_BLOCK_MIN_HITS distinct hits.
    for category, keywords in SKIP_NICHE_CATEGORIES.items():
        hits = [kw for kw in keywords if kw.lower() in weak_text]
        if len(hits) >= WEAK_BLOCK_MIN_HITS:
            matched = "+".join(k.strip() for k in hits[:2])
            return False, matched, category, ""

    # 4. Weak-zone positive classification: highest hit count wins.
    best_cat = "General / Other"
    best_score = 0
    for category, keywords in NICHE_CATEGORIES.items():
        score = sum(1 for kw in keywords if kw.lower() in weak_text)
        if score > best_score:
            best_cat, best_score = category, score

    return True, "", "", best_cat

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


def deobfuscate(text):
    """Turn 'info [at] domain [dot] com' style obfuscation into real emails."""
    text = OBFUSCATED_AT.sub("@", text)
    text = OBFUSCATED_DOT.sub(".", text)
    return text


def extract_emails(html, domain):
    """
    Extract emails from HTML. Returns list of (email, score) sorted by score desc.
    Decodes Cloudflare obfuscation, '[at]/[dot]' obfuscation, checks mailto:
    links and JSON-LD blocks, filters false positives.
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

    # JSON-LD structured data often carries a contact email.
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        if script.string:
            text += " " + script.string

    text = deobfuscate(text)

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
    t_start = time.time()
    checked_urls = set()
    all_emails = {}        # email -> (score, source_url)
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
            if email not in all_emails or score > all_emails[email][0]:
                all_emails[email] = (score, page_url)
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
        if time.time() - t_start > PHASE1_BUDGET_SEC:
            break
        html = try_fetch(url)
        absorb(html, url)

    # -> list of (email, score, source_url) sorted by score desc
    emails_sorted = sorted(
        [(e, s, u) for e, (s, u) in all_emails.items()],
        key=lambda x: -x[1],
    )
    return {
        "emails": emails_sorted,
        "pages_checked": pages_checked,
        "contact_form": contact_form,
        "contact_form_url": contact_form_url,
    }

# -- Phase 2: Wayback Machine --------------------------------------------------

def wayback_cdx(session, params):
    """
    Query the Wayback CDX API with light retry/backoff.
    v4.8: under domain-level concurrency many workers hit web.archive.org at
    once; it throttles (429/503) and drops connections. Retrying a couple of
    times with backoff protects Phase 2 recall. Returns parsed JSON or None.
    """
    for attempt in range(2):
        try:
            resp = session.get(WAYBACK_API, params=params, timeout=TIMEOUT)
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code in (429, 503):
                time.sleep(1.5 * (attempt + 1))
                continue
            return None
        except Exception:
            time.sleep(1.0 * (attempt + 1))
    return None


def phase2_wayback(domain, session):
    t_start = time.time()
    all_emails = {}        # email -> (score, source_url)
    pages_checked = 0
    snapshot_date = ""
    contact_form = ""
    contact_form_url = ""
    cdx_results = []

    kw_queries = ["contact", "about", "advertise", "editorial", "press"]
    for kw in kw_queries[:4]:
        params = {
            "url": domain + "/*" + kw + "*",
            "output": "json",
            "fl": "original,timestamp",
            "filter": "statuscode:200",
            "limit": "3",
            "collapse": "urlkey",
        }
        data = wayback_cdx(session, params)
        if data:
            for row in data[1:]:
                cdx_results.append((row[0], row[1]))

    params = {
        "url": domain,
        "output": "json",
        "fl": "original,timestamp",
        "filter": "statuscode:200",
        "limit": "2",
        "collapse": "urlkey",
    }
    data = wayback_cdx(session, params)
    if data:
        for row in data[1:]:
            cdx_results.append((row[0], row[1]))

    seen_orig = set()
    for orig_url, timestamp in cdx_results[:4]:
        if orig_url in seen_orig:
            continue
        if time.time() - t_start > PHASE2_BUDGET_SEC:
            break
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
                if email not in all_emails or score > all_emails[email][0]:
                    all_emails[email] = (score, wayback_url)
            if not contact_form:
                found, _ = detect_contact_form(html, orig_url)
                if found:
                    contact_form = "Unsure"
                    contact_form_url = orig_url

    emails_sorted = sorted(
        [(e, s, u) for e, (s, u) in all_emails.items()],
        key=lambda x: -x[1],
    )
    return {
        "emails": emails_sorted,
        "pages_checked": pages_checked,
        "snapshot_date": snapshot_date,
        "contact_form": contact_form,
        "contact_form_url": contact_form_url,
    }

# -- Phase 3: SMTP pattern verify ----------------------------------------------

def phase3_smtp(domain):
    """
    Returns dict: {"emails": [...], "catch_all": bool}

    Catch-all detection: probes a deliberately random address first. If the
    server accepts it (250), the domain accepts everything and SMTP pattern
    results cannot be trusted — catch_all=True and no pattern emails returned.

    v4.8 (throughput): opens ONE connection (connect/HELO/MAIL once) and reuses
    it for the catch-all probe and every pattern RCPT, instead of reconnecting
    13 times. FAIL-FAST: if the MX cannot be reached at all (e.g. outbound
    port 25 is blocked, as on GitHub-hosted runners), return immediately rather
    than looping every pattern against a dead socket. Timeout lowered to
    SMTP_TIMEOUT. Result semantics are unchanged from v4.7.

    NOTE: SMTP results are GUESSES — deliverable addresses, not addresses found
    on the site. They always get needs_manual_check.
    """
    try:
        mx_records = dns.resolver.resolve(domain, "MX")
        mx_host = str(
            sorted(mx_records, key=lambda r: r.preference)[0].exchange
        ).rstrip(".")
    except Exception:
        return {"emails": [], "catch_all": False}

    # --- Open a single SMTP session; bail out fast if it can't be established ---
    smtp = None
    try:
        smtp = smtplib.SMTP(timeout=SMTP_TIMEOUT)
        smtp.connect(mx_host, 25)
        smtp.helo("linkjuiceclub.com")
        smtp.mail("verify@linkjuiceclub.com")
    except Exception:
        if smtp is not None:
            try:
                smtp.close()
            except Exception:
                pass
        return {"emails": [], "catch_all": False}

    try:
        # --- Catch-all probe on the live connection ---
        try:
            code, _ = smtp.rcpt("xzqmverify_no_exist_99@" + domain)
            if code == 250:
                return {"emails": [], "catch_all": True}
        except Exception:
            # Connection died mid-probe — unverifiable, fail fast.
            return {"emails": [], "catch_all": False}

        # --- Pattern verification (reusing the same connection) ---
        verified = []
        for pattern in SMTP_PATTERNS:
            email = pattern + "@" + domain
            try:
                code, _ = smtp.rcpt(email)
                if code == 250:
                    score = EMAIL_SCORES.get(pattern, 10)
                    verified.append((email, score, ""))
            except Exception:
                # Server dropped the connection — stop, don't reconnect 12x.
                break
            time.sleep(0.2)

        return {"emails": sorted(verified, key=lambda x: -x[1]), "catch_all": False}
    finally:
        try:
            smtp.quit()
        except Exception:
            try:
                smtp.close()
            except Exception:
                pass

# -- Row builder ---------------------------------------------------------------

def build_row(domain, email_list, pages_checked, source,
              contact_form, contact_form_url, wayback_snapshot_date,
              confidence="", review_flag="", review_reason="", niche="",
              status=None):
    """email_list entries are (email, score, source_url) tuples."""
    emails = [e[0] for e in email_list]
    source_urls = [e[2] if len(e) > 2 else "" for e in email_list]
    if status is None:
        status = "verified" if emails else "no_email_found"
    return {
        "domain": domain,
        "primary_email": emails[0] if len(emails) > 0 else "",
        "email_2":       emails[1] if len(emails) > 1 else "",
        "email_3":       emails[2] if len(emails) > 2 else "",
        "all_emails":    " | ".join(emails),
        "email_source_url": source_urls[0] if source_urls else "",
        "pages_checked": pages_checked,
        "source":        source,
        "status":        status,
        "niche":         niche,
        "confidence":    confidence,
        "review_flag":   review_flag,
        "review_reason": review_reason,
        "contact_form":  contact_form,
        "contact_form_url": contact_form_url,
        "wayback_snapshot_date": wayback_snapshot_date,
        "date_scraped":  date.today().strftime("%d/%m/%Y"),
    }


def error_row(domain):
    return {
        "domain": domain,
        "primary_email": "", "email_2": "", "email_3": "", "all_emails": "",
        "email_source_url": "",
        "pages_checked": 0, "source": "", "status": "error", "niche": "",
        "confidence": "", "review_flag": "", "review_reason": "",
        "contact_form": "", "contact_form_url": "",
        "wayback_snapshot_date": "", "date_scraped": date.today().strftime("%d/%m/%Y"),
    }


def skip_row(domain, matched_keyword, niche_category):
    """Row written when phase0 determines the domain is an irrelevant niche."""
    return {
        "domain": domain,
        "primary_email": "", "email_2": "", "email_3": "", "all_emails": "",
        "email_source_url": "",
        "pages_checked": 0,
        "source": "blocked:" + matched_keyword,
        "status": "skipped_irrelevant",
        "niche": niche_category,
        "confidence": "", "review_flag": "", "review_reason": "",
        "contact_form": "", "contact_form_url": "",
        "wayback_snapshot_date": "", "date_scraped": date.today().strftime("%d/%m/%Y"),
    }

# -- Domain orchestrator -------------------------------------------------------

def scrape_domain(domain, session):
    contact_form = ""
    contact_form_url = ""
    wayback_snapshot_date = ""
    total_pages = 0

    # Phase 0: quick niche-relevance check — skip before any real scraping
    relevant, matched_kw, niche_cat, detected_niche = phase0_relevance(domain, session)
    if not relevant:
        print("[" + domain + "] SKIPPED — " + niche_cat + " (" + matched_kw + ")")
        return skip_row(domain, matched_kw, niche_cat)

    # Domains with no positive niche match always get a review flag.
    unclassified = detected_niche in ("", "General / Other")
    base_reasons = ["unclassified_niche"] if unclassified else []

    print("[" + domain + "] Niche: " + (detected_niche or "unknown (homepage unreachable)"))
    print("[" + domain + "] Phase 1: HTTP scraper...")
    p1 = phase1_http(domain, session)
    total_pages += p1["pages_checked"]

    if p1["contact_form"]:
        contact_form = p1["contact_form"]
        contact_form_url = p1["contact_form_url"]

    if p1["emails"]:
        # Same-domain emails first; off-domain emails kept but never verified.
        same_dom = [e for e in p1["emails"] if email_matches_domain(e[0], domain)]
        off_dom = [e for e in p1["emails"] if not email_matches_domain(e[0], domain)]
        ordered = same_dom + off_dom

        if same_dom:
            status = "verified"
            confidence = "high"
            reasons = list(base_reasons)
        else:
            status = "needs_manual_check"
            confidence = "medium"
            reasons = base_reasons + ["domain_mismatch"]

        review_flag = "yes" if reasons else ""
        print("[" + domain + "] Phase 1 found " + str(len(ordered)) + " emails"
              + " (" + str(len(same_dom)) + " on-domain) -> " + status)
        return build_row(domain, ordered, total_pages, "scraper",
                         contact_form, contact_form_url, "",
                         confidence=confidence, review_flag=review_flag,
                         review_reason="; ".join(reasons), niche=detected_niche,
                         status=status)

    print("[" + domain + "] Phase 2: Wayback Machine...")
    p2 = phase2_wayback(domain, session)
    total_pages += p2["pages_checked"]
    wayback_snapshot_date = p2["snapshot_date"]

    if p2["contact_form"] and not contact_form:
        contact_form = p2["contact_form"]
        contact_form_url = p2["contact_form_url"]

    if p2["emails"]:
        # Archive emails may be stale — NEVER verified.
        reasons = base_reasons + ["wayback_archive"]
        print("[" + domain + "] Phase 2 found " + str(len(p2["emails"]))
              + " emails (archive) -> needs_manual_check")
        return build_row(domain, p2["emails"], total_pages, "wayback_unsure",
                         contact_form, contact_form_url, wayback_snapshot_date,
                         confidence="low", review_flag="yes",
                         review_reason="; ".join(reasons), niche=detected_niche,
                         status="needs_manual_check")

    enable_smtp = os.environ.get("ENABLE_SMTP_VERIFY", "false").lower() == "true"
    if enable_smtp:
        print("[" + domain + "] Phase 3: SMTP pattern verify...")
        p3 = phase3_smtp(domain)
        if p3["catch_all"]:
            print("[" + domain + "] Catch-all domain — flagging for manual review.")
            reasons = base_reasons + ["smtp_catchall"]
            return build_row(domain, [], total_pages, "smtp_catchall",
                             contact_form, contact_form_url, wayback_snapshot_date,
                             confidence="low", review_flag="yes",
                             review_reason="; ".join(reasons), niche=detected_niche,
                             status="no_email_found")
        if p3["emails"]:
            # SMTP results are deliverable GUESSES, not on-site emails — NEVER verified.
            reasons = base_reasons + ["smtp_guess"]
            print("[" + domain + "] Phase 3 verified " + str(len(p3["emails"]))
                  + " deliverable guesses -> needs_manual_check")
            return build_row(domain, p3["emails"], total_pages, "smtp_guess",
                             contact_form, contact_form_url, wayback_snapshot_date,
                             confidence="low", review_flag="yes",
                             review_reason="; ".join(reasons), niche=detected_niche,
                             status="needs_manual_check")

    print("[" + domain + "] No emails found -> manual check.")
    reasons = base_reasons + ["no_email_found"]
    return build_row(domain, [], total_pages, "", contact_form, contact_form_url,
                     wayback_snapshot_date,
                     review_flag="yes", review_reason="; ".join(reasons),
                     niche=detected_niche, status="no_email_found")

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


def scrape_one(raw_domain):
    """
    Worker entry point: scrape a single domain with its own session.
    Each worker gets an isolated requests.Session (Sessions are not designed to
    be shared across threads). Never raises — a fatal error becomes an
    error_row so one bad domain can't take down the pool.
    """
    domain = normalise(raw_domain)
    session = make_session()
    try:
        return scrape_domain(domain, session)
    except Exception as exc:
        print("[" + domain + "] Fatal: " + str(exc))
        return error_row(domain)
    finally:
        try:
            session.close()
        except Exception:
            pass


def main():
    domains = load_domains()
    if not domains:
        print("No domains to process. Add them to " + DOMAINS_FILE)
        return

    total = len(domains)
    print("Starting scraper v4.9 -- " + str(total) + " domains, "
          + str(MAX_WORKERS) + " parallel workers.")

    # v4.8: domains run in parallel. Output is written under a lock and flushed
    # per row (resilient if the job is killed). Rows are in COMPLETION order,
    # not input order — each row is still labelled by its domain.
    write_lock = threading.Lock()
    done = 0

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        f.flush()

        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_domain = {
                executor.submit(scrape_one, raw_domain): raw_domain
                for raw_domain in domains
            }
            for future in concurrent.futures.as_completed(future_to_domain):
                raw_domain = future_to_domain[future]
                try:
                    row = future.result()
                except Exception as exc:
                    print("[" + normalise(raw_domain) + "] Fatal: " + str(exc))
                    row = error_row(normalise(raw_domain))
                with write_lock:
                    writer.writerow(row)
                    f.flush()
                    done += 1
                    print("[" + str(done) + "/" + str(total) + "] "
                          + row.get("domain", "") + " -> " + row.get("status", ""))

    print("\nDone. Results saved to " + OUTPUT_FILE)


if __name__ == "__main__":
    main()
