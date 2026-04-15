"""
Test Email Sender
=================
Sends a single test email from Eszter's account to gary@linkjuiceclub.com
to verify SMTP is working correctly.

Run via GitHub Actions: Actions → Test Email → Run workflow
"""

import os, smtplib, logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_SERVER = "smtp.office365.com"
SMTP_PORT   = 587

def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s")

    user = os.environ.get("SMTP_USER_1", "").strip()
    pwd  = os.environ.get("SMTP_PASS_1", "").strip()

    if not user or not pwd:
        raise ValueError("SMTP_USER_1 or SMTP_PASS_1 not set. Check GitHub Secrets.")

    to_email = "gary@linkjuiceclub.com"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "✅ Outreach Agent — SMTP Test Successful"
    msg["From"]    = f"Eszter Ivan <{user}>"
    msg["To"]      = to_email

    body = f"""\
Hi Gary,

This is a test email from the Outreach Agent pipeline.

If you're reading this, the SMTP connection is working correctly for:

  Sender : Eszter Ivan <{user}>
  Server : {SMTP_SERVER}:{SMTP_PORT}

The system is ready to send outreach emails.

— Outreach Agent
"""
    msg.attach(MIMEText(body, "plain"))

    print(f"Connecting to {SMTP_SERVER}:{SMTP_PORT}...")
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        print(f"Logging in as {user}...")
        server.login(user, pwd)
        print(f"Sending to {to_email}...")
        server.sendmail(user, to_email, msg.as_string())

    print(f"\n✅ Test email sent successfully to {to_email}")
    print(f"   From: Eszter Ivan <{user}>")

if __name__ == "__main__":
    main()
