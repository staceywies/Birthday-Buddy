import os
import json
from datetime import date, datetime
import requests
from dotenv import load_dotenv

load_dotenv()

# ---------------------------
# Birthday calculation helpers
# ---------------------------

def days_until_birthday(birthday_str):
    """
    Returns number of days until next birthday.
    Birthday format: MM-DD
    """
    today = date.today()
    bday = datetime.strptime(birthday_str, "%m-%d").date().replace(year=today.year)

    # If birthday already passed this year, use next year
    if bday < today:
        bday = bday.replace(year=today.year + 1)

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
    """
    url = "https://api.brevo.com/v3/smtp/email"

    payload = {
        "sender": {"name": "Birthday Bot", "email": os.getenv("FROM_EMAIL")},
        "to": [{"email": os.getenv("TO_EMAIL")}],
        "subject": "🎉 Birthday Reminder",
        "textContent": message
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": os.getenv("BREVO_API_KEY")
    }

    try:
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 201:
            print("✅ Email successfully sent!")
        elif response.status_code == 400:
            print("⚠️ Bad request — check payload fields.")
            print(response.text)
        elif response.status_code == 401:
            print("🚫 Unauthorized — check your API key.")
        elif response.status_code == 429:
            print("⏳ Rate limited — slow down.")
        else:
            print(f"❌ Unexpected error ({response.status_code}): {response.text}")

    except requests.exceptions.RequestException as e:
        print("💥 Network error:", e)


# ---------------------------
# Load birthday data
# ---------------------------

birthday_data_str = os.getenv("BIRTHDAY_DATA")
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

if messages:
    combined_message = "\n".join(messages)
    send_email(combined_message)
else:
    print("No birthdays to remind today.")


# ---------------------------
# Daily log
# ---------------------------

with open("log.txt", "a") as log:
    entry = (
        f"{date.today()} - "
        f"{'; '.join(messages) if messages else 'No reminders today'}\n"
    )
    log.write(entry)
