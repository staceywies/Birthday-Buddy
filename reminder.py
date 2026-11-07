import os
import sys
import json
from datetime import date, datetime
import requests
from dotenv import load_dotenv

load_dotenv()

# ---------------------------
# Birthday calculation helpers
# ---------------------------

def birthday_in_year(birthday_str, year):
    """
    Returns the birthday as a date in the given year.
    Feb 29 birthdays fall back to Feb 28 in non-leap years.
    Birthday format: MM-DD
    """
    month, day = datetime.strptime(birthday_str, "%m-%d").timetuple()[1:3]
    try:
        return date(year, month, day)
    except ValueError:
        return date(year, 2, 28)


def days_until_birthday(birthday_str):
    """
    Returns number of days until next birthday.
    Birthday format: MM-DD
    """
    today = date.today()
    bday = birthday_in_year(birthday_str, today.year)

    # If birthday already passed this year, use next year
    if bday < today:
        bday = birthday_in_year(birthday_str, today.year + 1)

    return (bday - today).days


def should_remind(days_left, status):
    """
    Determines whether a reminder should be sent based on relationship status.
    """
    if days_left == 0:
        return True

    if status == "bestie" and days_left in [30, 7, 0]:
        return True

    if status == "close" and days_left in [7, 0]:
        return True

    return False


# ---------------------------
# Message creation
# ---------------------------

def make_message(name, days_left, birthday_str):
    """
    Creates the appropriate reminder message for a single person.
    """
    if days_left == 0:
        return f"🎂 It's {name}'s birthday today! ({birthday_str})"
    if days_left == 7:
        return f"📅 {name}'s birthday is in 1 week. ({birthday_str})"
    if days_left == 30:
        return f"🗓️ {name}'s birthday is in 30 days. ({birthday_str})"
    return None


# ---------------------------
# Email sending
# ---------------------------

def send_email(message):
    """
    Sends a single combined email via Brevo.
    Returns True if Brevo accepted the email, False otherwise.
    """
    url = "https://api.brevo.com/v3/smtp/email"

    # .strip() removes accidental spaces/newlines from pasted secrets
    api_key = (os.getenv("BREVO_API_KEY") or "").strip()
    from_email = (os.getenv("FROM_EMAIL") or "").strip()
    to_email = (os.getenv("TO_EMAIL") or "").strip()

    if not api_key or not from_email or not to_email:
        print("⚠️ Missing BREVO_API_KEY, FROM_EMAIL, or TO_EMAIL secret.")
        return False

    payload = {
        "sender": {"name": "Birthday Bot", "email": from_email},
        "to": [{"email": to_email}],
        "subject": "🎉 Birthday Reminder",
        "textContent": message
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": api_key
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)

        if response.status_code == 201:
            print("✅ Email successfully sent!")
            return True
        elif response.status_code == 400:
            print("⚠️ Bad request — check payload fields.")
        elif response.status_code == 401:
            print("🚫 Unauthorized — check your API key.")
        elif response.status_code == 429:
            print("⏳ Rate limited — slow down.")
        else:
            print(f"❌ Unexpected error ({response.status_code})")

        # Brevo's explanation of what went wrong
        print(response.text)
        return False

    except requests.exceptions.RequestException as e:
        print("💥 Network error:", e)
        return False


# ---------------------------
# Load birthday data
# ---------------------------

birthday_data_str = os.getenv("BIRTHDAY_DATA")
if not birthday_data_str:
    print("⚠️ BIRTHDAY_DATA secret is missing or empty.")
    sys.exit(1)

friends = json.loads(birthday_data_str)


# ---------------------------
# Process reminders
# ---------------------------

messages = []

for friend in friends:
    days_left = days_until_birthday(friend["birthday"])

    if should_remind(days_left, friend["status"]):
        msg = make_message(friend["name"], days_left, friend["birthday"])
        if msg:
            messages.append(msg)

# ---------------------------
# Send combined email
# ---------------------------

email_ok = True

if messages:
    combined_message = "\n".join(messages)
    email_ok = send_email(combined_message)
else:
    print("No birthdays to remind today.")


# ---------------------------
# Daily log
# ---------------------------

with open("log.txt", "a") as log:
    if messages:
        status_note = "" if email_ok else " [EMAIL FAILED]"
        entry = f"{date.today()} - {'; '.join(messages)}{status_note}\n"
    else:
        entry = f"{date.today()} - No reminders today\n"
    log.write(entry)

# Make the workflow run go red if the email failed
if not email_ok:
    sys.exit(1)