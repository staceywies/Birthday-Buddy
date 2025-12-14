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
