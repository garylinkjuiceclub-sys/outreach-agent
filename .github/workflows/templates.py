"""
Email Templates — Backlink Outreach
=====================================
One template per topic category, with personalisation variables.
Variables available in every template:
  {domain}        — the target website (e.g. givemesport.com)
  {site_name}     — cleaned site name (e.g. GiveMeSport)
  {sender_name}   — name of the sending account
  {sender_email}  — email of the sending account

Edit the SUBJECT and BODY for each topic below.
Keep {variables} exactly as written — they are replaced automatically.
"""

def get_site_name(domain: str) -> str:
    """Convert domain to readable site name. e.g. give-me-sport.com -> Give Me Sport"""
    name = domain.split(".")[0]
    name = name.replace("-", " ").replace("_", " ")
    return name.title()


# ══════════════════════════════════════════════════════════════════════════════
# TEMPLATES — edit subject and body freely, keep {variables} intact
# ══════════════════════════════════════════════════════════════════════════════

TEMPLATES = {

    "Gambling": {
        "subject": "Link placement opportunity — casino/gambling content",
        "body": """\
Hi {site_name} team,

I came across {domain} while researching link placement opportunities in the iGaming space and wanted to reach out directly.

We work with several licensed online casino brands and are looking for quality placements on established sites like yours. We're open to sponsored content, editorial mentions, or whatever format works best for your editorial guidelines.

If this is something you'd consider, I'd love to discuss rates and any content requirements you have.

Best regards,
{sender_name}
{sender_email}

---
To opt out of future emails, simply reply with "unsubscribe".
""",
    },

    "Sports": {
        "subject": "Content partnership — sports & betting",
        "body": """\
Hi {site_name} team,

I hope this finds you well. I'm reaching out because {domain} looks like a great fit for a content partnership we're exploring.

We represent a number of licensed sports betting and casino brands, and we're looking to place high-quality, relevant content on sports-focused publications. This could be a sponsored article, a product mention within existing content, or a dedicated review piece — entirely up to you.

Would you be open to a quick conversation about what might work?

Best,
{sender_name}
{sender_email}

---
To opt out of future emails, reply with "unsubscribe".
""",
    },

    "Gaming/eSports": {
        "subject": "Partnership opportunity — gaming & betting",
        "body": """\
Hi {site_name} team,

I've been following {domain} for a while — great coverage of the gaming space.

I work with several licensed online casino and gaming brands who are keen to reach an engaged gaming audience. We're looking for editorial placements, sponsored content, or review opportunities on sites like yours.

If you have a media pack or rate card, I'd love to take a look. Otherwise happy to chat about what works for your audience.

Cheers,
{sender_name}
{sender_email}

---
To opt out of future emails, reply with "unsubscribe".
""",
    },

    "Finance": {
        "subject": "Editorial opportunity — online gaming & finance",
        "body": """\
Hi {site_name} team,

I'm reaching out on behalf of several regulated online casino brands with a strong financial/responsible gaming angle.

We're exploring editorial placements on finance and money-focused publications — whether that's a sponsored feature, a product comparison mention, or a relevant link within existing content. We're flexible on format and happy to match your editorial standards.

Would this be of interest? Happy to share more detail on the brands and content we have available.

Kind regards,
{sender_name}
{sender_email}

---
To opt out, reply with "unsubscribe".
""",
    },

    "Tech": {
        "subject": "Link opportunity — online gaming platforms",
        "body": """\
Hi {site_name} team,

Quick outreach to see if {domain} would be open to a sponsored content or link placement opportunity.

We work with a portfolio of licensed online casino and gaming brands — all regulated, well-established operators. We're looking to place relevant content on quality tech and digital publications, and your site stood out as a strong fit.

If you have availability or a rate card, I'd love to hear from you.

Best,
{sender_name}
{sender_email}

---
To opt out of future emails, reply with "unsubscribe".
""",
    },

    "Entertainment": {
        "subject": "Brand partnership — entertainment & gaming",
        "body": """\
Hi {site_name} team,

I came across {domain} and thought there could be a good fit for a partnership we're working on.

We represent a number of well-known online casino and entertainment brands looking to reach lifestyle and entertainment audiences. We're open to sponsored articles, product features, newsletter mentions — whatever works best for your readership.

Let me know if you'd like to explore this further.

Best,
{sender_name}
{sender_email}

---
To opt out, reply with "unsubscribe".
""",
    },

    "Magazines": {
        "subject": "Editorial partnership — casino & lifestyle brands",
        "body": """\
Hi {site_name} team,

I'm getting in touch to explore whether {domain} would consider a sponsored editorial placement or brand partnership with one of our casino clients.

We work with several licensed, reputable operators and are looking for quality placements in lifestyle and magazine-style publications. We're happy to work within your existing editorial formats and guidelines.

Do you have a media pack or would you be open to a brief chat?

Warm regards,
{sender_name}
{sender_email}

---
To opt out of future emails, reply with "unsubscribe".
""",
    },

    "General News": {
        "subject": "Sponsored content opportunity — online gaming",
        "body": """\
Hi {site_name} team,

I hope you're well. I'm reaching out to see whether {domain} accepts sponsored content or brand placements from regulated online gaming companies.

We work with a portfolio of licensed casino operators and are looking for editorial opportunities on established news and media sites. We're flexible on format — sponsored articles, product mentions, or relevant links within existing content all work for us.

Happy to share more detail if this is something you'd consider.

Best,
{sender_name}
{sender_email}

---
To opt out, reply with "unsubscribe".
""",
    },

    "Global News": {
        "subject": "Sponsored content — licensed casino brands",
        "body": """\
Hi {site_name} team,

I'm reaching out on behalf of a portfolio of licensed online casino brands. We're actively looking for sponsored content and editorial placement opportunities on established international news and media platforms.

{domain} stood out as a strong fit given your audience reach. We're flexible on format and happy to discuss rates and content requirements that work for your publication.

Would you be open to exploring this?

Kind regards,
{sender_name}
{sender_email}

---
To opt out of future emails, reply with "unsubscribe".
""",
    },

    "Travel": {
        "subject": "Partnership opportunity — gaming & lifestyle",
        "body": """\
Hi {site_name} team,

I came across {domain} and wanted to reach out about a potential content partnership.

We work with several licensed online casino brands that appeal to a lifestyle and travel-oriented audience — think entertainment, leisure, and online gaming. We're looking for quality placements on travel and lifestyle sites and would love to explore what might work for your readers.

If you're open to sponsored content or partnerships, I'd love to hear what you have available.

Best,
{sender_name}
{sender_email}

---
To opt out, reply with "unsubscribe".
""",
    },

    "Crypto": {
        "subject": "Link placement — crypto-friendly casino brands",
        "body": """\
Hi {site_name} team,

Quick note to see if {domain} would be open to a sponsored placement or link opportunity.

We work with a number of online casino brands that accept crypto and cater to a digitally savvy, finance-forward audience — which felt like a natural match for your readership.

If you accept sponsored content or editorial placements, I'd love to discuss further.

Cheers,
{sender_name}
{sender_email}

---
To opt out of future emails, reply with "unsubscribe".
""",
    },

    # Fallback for unknown/unmatched topics
    "Unknown": {
        "subject": "Link placement opportunity",
        "body": """\
Hi {site_name} team,

I'm reaching out to see if {domain} would be open to a sponsored content or link placement opportunity with one of our licensed online casino clients.

We work with several established, regulated operators and are always looking for quality sites to partner with. Happy to share more detail on the brands and content we have available.

Would you be open to a quick conversation?

Best,
{sender_name}
{sender_email}

---
To opt out of future emails, reply with "unsubscribe".
""",
    },
}


def get_template(topic: str) -> dict:
    """Return subject + body for a given topic. Falls back to Unknown."""
    return TEMPLATES.get(topic, TEMPLATES["Unknown"])


def render(template: dict, domain: str, sender_name: str, sender_email: str) -> tuple[str, str]:
    """Fill in variables and return (subject, body)."""
    site_name = get_site_name(domain)
    variables = {
        "domain":       domain,
        "site_name":    site_name,
        "sender_name":  sender_name,
        "sender_email": sender_email,
    }
    subject = template["subject"].format(**variables)
    body    = template["body"].format(**variables)
    return subject, body
