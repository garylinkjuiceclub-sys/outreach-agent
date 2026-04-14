"""
Email Sender — Backlink Outreach
==================================
Sends up to 100 emails per account per day across 4 accounts.
Reads contacts from outreach_contacts.csv (output of run_pipeline.py).
Tracks sent emails in sent_log.csv so contacts are never emailed twice.

Schedule: runs Tuesday–Friday via GitHub Actions.

Environment variables required (set as GitHub Secrets):
  SMTP_USER_1  SMTP_PASS_1   (eszter.ivan@linkjuiceclub.com)
  SMTP_USER_2  SMTP_PASS_2   (adnan.ajanovic@linkjuiceclub.com)
  SMTP_USER_3  SMTP_PASS_3   (benisa@linkjuiceclub.com)
  SMTP_USER_4  SMTP_PASS_4   (asmir@linkjuiceclub.com)
"""

import os, csv, smtplib, time, random, logging
from datetime import datetime, date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from templates import get_template, render

# ══════════════════════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════════════════════

SMTP_SERVER   = "smtp.office365.com"
SMTP_PORT     = 587
DAILY_LIMIT   = 100          # Max emails per account per day
DELAY_MIN     = 45           # Min seconds between sends (per account)
DELAY_MAX     = 90           # Max seconds — natural spacing, avoids pattern flags

CONTACTS_FILE = "output/outreach_contacts.csv"   # Written by run_pipeline.py
SENT_LOG      = "output/sent_log.csv"            # Tracks every email sent

SENDER_NAMES  = {
    1: "Eszter Ivan",
    2: "Adnan Ajanovic",
    3: "Benisa Bibuljica",
    4: "Asmir Novalija",
}

# ── Load accounts from environment ───────────────────────────────────────────

def load_accounts():
    accounts = []
    for i in range(1, 5):
        user = os.environ.get(f"SMTP_USER_{i}", "").strip()
        pwd  = os.environ.get(f"SMTP_PASS_{i}", "").strip()
        if user and pwd:
            accounts.append({
                "id":    i,
                "email": user,
                "pass":  pwd,
                "name":  SENDER_NAMES.get(i, f"Account {i}"),
                "sent_today": 0,
            })
    if not accounts:
        raise ValueError("No SMTP accounts found. Check SMTP_USER_1..4 and SMTP_PASS_1..4 secrets.")
    return accounts


# ══════════════════════════════════════════════════════════════════════════════
# SENT LOG
# ══════════════════════════════════════════════════════════════════════════════

def load_sent_log() -> set:
    """Return set of domains already emailed."""
    sent = set()
    if Path(SENT_LOG).exists():
        with open(SENT_LOG, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                sent.add(row["domain"].strip().lower())
    return sent


def log_sent(domain: str, email: str, sender: str, topic: str, status: str):
    """Append a send record to the log."""
    Path(SENT_LOG).parent.mkdir(parents=True, exist_ok=True)
    file_exists = Path(SENT_LOG).exists()
    with open(SENT_LOG, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["date","domain","email","sender","topic","status"])
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "date":    datetime.now().strftime("%Y-%m-%d %H:%M"),
            "domain":  domain,
            "email":   email,
            "sender":  sender,
            "topic":   topic,
            "status":  status,
        })


# ══════════════════════════════════════════════════════════════════════════════
# SENDING
# ══════════════════════════════════════════════════════════════════════════════

def send_email(account: dict, to_email: str, subject: str, body: str) -> bool:
    """Send a single plain-text email. Returns True on success."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"{account['name']} <{account['email']}>"
        msg["To"]      = to_email
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=20) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(account["email"], account["pass"])
            server.sendmail(account["email"], to_email, msg.as_string())
        return True

    except smtplib.SMTPAuthenticationError:
        logging.error(f"  AUTH FAILED for {account['email']} — check password in GitHub Secrets")
        return False
    except smtplib.SMTPRecipientsRefused:
        logging.warning(f"  Recipient refused: {to_email}")
        return False
    except Exception as e:
        logging.error(f"  Send error ({to_email}): {e}")
        return False


def load_contacts() -> list:
    """Load contacts from CSV, return list of dicts."""
    if not Path(CONTACTS_FILE).exists():
        raise FileNotFoundError(
            f"Contacts file not found: {CONTACTS_FILE}\n"
            "Run run_pipeline.py first to generate the outreach list."
        )
    contacts = []
    with open(CONTACTS_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            email = row.get("best_email", "").strip()
            domain = row.get("domain", "").strip().lower()
            if email and "@" in email and domain:
                contacts.append(row)
    return contacts


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(message)s",
        datefmt="%H:%M:%S",
    )

    print("=" * 60)
    print(f"  Outreach Email Sender — {date.today().strftime('%A %d %B %Y')}")
    print("=" * 60)

    accounts   = load_accounts()
    sent_log   = load_sent_log()
    contacts   = load_contacts()

    # Filter to unsent contacts with an email
    pending = [
        c for c in contacts
        if c["domain"].strip().lower() not in sent_log
        and c.get("best_email", "").strip()
    ]

    total_capacity = len(accounts) * DAILY_LIMIT
    to_send = pending[:total_capacity]

    print(f"\n  Accounts loaded  : {len(accounts)}")
    print(f"  Total pending    : {len(pending)}")
    print(f"  Sending today    : {len(to_send)} (cap: {total_capacity})")
    print()

    if not to_send:
        print("  No pending contacts to send to today. Run pipeline to refresh the list.")
        return

    # Distribute contacts round-robin across accounts
    queues = {a["id"]: [] for a in accounts}
    for i, contact in enumerate(to_send):
        acct = accounts[i % len(accounts)]
        queues[acct["id"]].append(contact)

    sent_total   = 0
    failed_total = 0

    for account in accounts:
        queue = queues[account["id"]]
        if not queue:
            continue

        print(f"  ── {account['email']} ({len(queue)} to send) ──")

        for contact in queue:
            domain = contact["domain"].strip().lower()
            email  = contact.get("best_email", "").strip()
            topic  = contact.get("topic_category", "Unknown")

            template       = get_template(topic)
            subject, body  = render(template, domain, account["name"], account["email"])

            success = send_email(account, email, subject, body)
            status  = "sent" if success else "failed"

            log_sent(domain, email, account["email"], topic, status)

            if success:
                sent_total += 1
                print(f"    ✓ {domain:35s} → {email}")
            else:
                failed_total += 1
                print(f"    ✗ {domain:35s} → FAILED")

            # Polite delay between sends
            if queue.index(contact) < len(queue) - 1:
                delay = random.uniform(DELAY_MIN, DELAY_MAX)
                time.sleep(delay)

        print()

    print("=" * 60)
    print(f"  DONE  |  Sent: {sent_total}  |  Failed: {failed_total}")
    print(f"  Log   →  {SENT_LOG}")
    print("=" * 60)


if __name__ == "__main__":
    main()
