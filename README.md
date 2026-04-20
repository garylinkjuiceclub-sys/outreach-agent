# Backlink Outreach Pipeline

Automated weekly system that:
1. Pulls competitor backlink gap data from Ahrefs (every Monday)
2. Filters by DR, traffic, and topic relevance
3. Scrapes contact emails from target sites
4. Outputs a clean Excel file every Monday morning
5. Sends up to 400 personalised outreach emails per day (Tuesday–Friday)

**Total cost:** £0/week beyond your existing Ahrefs plan.  
**Runs on:** GitHub's servers — nothing touches your device.

---

## One-time setup (takes ~15 minutes)

### Step 1 — Create a GitHub account
Go to [github.com](https://github.com) and sign up for a free account if you don't have one.

### Step 2 — Create a new private repository
1. Click the **+** icon (top right) → **New repository**
2. Name it `32red-outreach` (or anything you like)
3. Set it to **Private**
4. Click **Create repository**

### Step 3 — Upload the files
You have two options:

**Option A — GitHub web interface (no Git needed):**
1. In your new repo, click **Add file** → **Upload files**
2. Upload all `.py` files: `run_pipeline.py`, `send_emails.py`, `templates.py`
3. Upload `requirements.txt`
4. Click **Add file** → **Create new file**, name it `.github/workflows/weekly_scrape.yml`, paste the contents of `weekly_scrape.yml`, click **Commit changes**
5. Repeat for `.github/workflows/send_emails.yml`

**Option B — Git command line:**
```bash
git clone https://github.com/YOUR_USERNAME/32red-outreach.git
cd 32red-outreach
# Copy all files into this folder, then:
git add .
git commit -m "Initial pipeline setup"
git push
```

### Step 4 — Add your Ahrefs API key
1. In your repo, go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Name: `AHREFS_API_KEY`
4. Value: your Ahrefs API key (Ahrefs → Settings → API)
5. Click **Add secret**

### Step 5 — Add your email account secrets
Add 8 secrets — one username + password pair per sending account:

| Secret name   | Value                               |
|---------------|-------------------------------------|
| `SMTP_USER_1` | `eszter.ivan@linkjuiceclub.com`     |
| `SMTP_PASS_1` | Eszter's Microsoft 365 password     |
| `SMTP_USER_2` | `adnan.ajanovic@linkjuiceclub.com`  |
| `SMTP_PASS_2` | Adnan's Microsoft 365 password      |
| `SMTP_USER_3` | `benisa@linkjuiceclub.com`          |
| `SMTP_PASS_3` | Benisa's Microsoft 365 password     |
| `SMTP_USER_4` | `asmir@linkjuiceclub.com`           |
| `SMTP_PASS_4` | Asmir's Microsoft 365 password      |

> **Note on GoDaddy M365 accounts:** SMTP AUTH is enabled by default on GoDaddy-hosted
> Microsoft 365 mailboxes when IMAP is on. No extra configuration is needed — just use
> the normal account password as `SMTP_PASS_*`. If you later change a password, update
> the corresponding GitHub Secret.

That's it. The pipeline is live.

---

## How the weekly schedule works

| Day       | What runs                                              |
|-----------|--------------------------------------------------------|
| Monday    | Scrape job — pulls Ahrefs data, finds emails, creates Excel |
| Tuesday   | Email send — up to 400 emails across 4 accounts       |
| Wednesday | Email send — up to 400 emails across 4 accounts       |
| Thursday  | Email send — up to 400 emails across 4 accounts       |
| Friday    | Email send — up to 400 emails across 4 accounts       |

All times are **8:00am UTC** (9:00am UK time in winter, 8:00am in summer).

The scraper writes `output/outreach_contacts.csv` on Monday and commits it to the
repo. The daily sender reads from that file Tuesday–Friday. A `sent_log.csv` is
maintained so the same domain is never emailed twice, even across weeks.

---

## How to get your Excel results

### Automatic (every Monday)
GitHub runs the pipeline at 7:00am UTC every Monday automatically.

### Manual run (any time)
1. Go to your repo → **Actions** tab
2. Click **Weekly Outreach List** in the left panel
3. Click **Run workflow** → **Run workflow**
4. Wait ~60–90 minutes (depending on list size)
5. Click the completed run → scroll down to **Artifacts**
6. Download the Excel file

---

## Adjusting the pipeline

All settings are at the top of `run_pipeline.py`:

| Setting | Default | What it does |
|---|---|---|
| `ROWS_PER_COMPETITOR` | 500 | Referring domains pulled per competitor. 500 × 10 = up to 5,000 gap domains. Increase to 1000 for ~10K. |
| `MIN_DR` | 10 | Minimum Domain Rating to include |
| `MIN_TRAFFIC` | 1000 | Minimum monthly organic traffic |
| `SCRAPE_WORKERS` | 8 | Concurrent scrape threads. Higher = faster but more likely to trigger rate limits |
| `COMPETITORS` | 10 sites | Edit this list to add/remove competitors |

To change a setting, edit `run_pipeline.py` directly in GitHub (click the file → pencil icon) and commit.

Email sending settings are at the top of `send_emails.py`:

| Setting | Default | What it does |
|---|---|---|
| `DAILY_LIMIT` | 100 | Max emails per account per day (400 total across 4 accounts) |
| `DELAY_MIN` | 45 | Minimum seconds between sends per account |
| `DELAY_MAX` | 90 | Maximum seconds between sends per account |

---

## Customising email templates

All outreach email copy lives in `templates.py`. There is one template per topic category:

- Gambling, Sports, Gaming/eSports, Finance, Tech, Entertainment, Magazines,
  General News, Global News, Travel, Crypto, Unknown (fallback)

Each template has a **subject** and **body**. Available variables — use these exactly
as written and they'll be filled in automatically for each contact:

| Variable | Example output |
|---|---|
| `{domain}` | `givemesport.com` |
| `{site_name}` | `Givemesport` |
| `{sender_name}` | `Eszter Ivan` |
| `{sender_email}` | `eszter.ivan@linkjuiceclub.com` |

To edit a template, open `templates.py` in GitHub (pencil icon), find the relevant
topic key, and edit the `"subject"` or `"body"` string. Commit when done — the next
send run will pick up the new copy automatically.

> **Keep all `{variable}` placeholders intact** — removing or misspelling them will
> cause the sender to crash on that template.

---

## The sent log

`output/sent_log.csv` is committed back to the repo after each sending run. It records:

| Column | Example |
|---|---|
| `date` | `2026-04-15 08:23` |
| `domain` | `givemesport.com` |
| `email` | `partnerships@givemesport.com` |
| `sender` | `eszter.ivan@linkjuiceclub.com` |
| `topic` | `Sports` |
| `status` | `sent` / `failed` |

A domain that appears in this log — even as `failed` — will not be emailed again
unless you manually remove it from the log. This prevents accidental double-sends.

To reset and re-send to a domain: open `output/sent_log.csv` in GitHub, delete that
domain's row, and commit.

---

## Ahrefs API units used per run

| Action | Units |
|---|---|
| 10 competitors × 500 rows @ 14 units/row | ~70,000 |
| 32red.com existing links (2,000 rows) | ~28,000 |
| **Total per weekly run** | **~98,000** |
| Your monthly budget | 500,000 |
| Remaining for other use | ~108,000/month |

Running at 1,000 rows per competitor (for ~10K domains) doubles the above — still within budget at ~296,000/month.

---

## Output files

Each scrape run produces a dated Excel file (e.g. `32red_outreach_2026-04-21.xlsx`) with three sheets:

- **Outreach List** — all domains with DR, traffic, topic, emails, opportunity type
- **Emails Only** — clean filtered list of domains where an email was found
- **Summary** — counts by topic, opportunity type, and total

---

## Topics included

The scraper scores each domain against these accepted categories:

Gambling · Sports · Tech · Gaming/eSports · Travel · Finance · Crypto · General News · Global News · Entertainment · Magazines

Domains that don't match any topic get scored as "Unknown" and appear at the bottom of the list — review manually or discard.

---

## Safety notes

- The scraper uses polite request delays (0.3–0.8s between calls) to avoid overloading sites
- The email sender uses 45–90 second random delays between sends to avoid pattern detection
- Accounts are capped at 100 emails/day — well within safe limits for warmed GoDaddy M365 accounts
- Running on GitHub's servers means your home/office IP is never exposed
- All credentials (Ahrefs key, SMTP passwords) are stored as encrypted GitHub Secrets — never visible in logs or code
- Every email includes an unsubscribe instruction ("reply with unsubscribe")
