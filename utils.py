"""utils.py - input validation and small helper functions used by every module."""
from datetime import date, datetime


def get_number(prompt, kind=float, low=None, high=None):
    """Keep asking until the user enters a valid number between low and high."""
    while True:
        text = input(prompt).strip()
        try:
            value = kind(text)
        except ValueError:
            print("  Invalid input. Please enter a valid number.")
            continue
        if value != value or value in (float("inf"), float("-inf")):
            print("  Invalid input. Please enter a normal number.")
            continue
        if low is not None and value < low:
            print(f"  Value must be at least {low}.")
            continue
        if high is not None and value > high:
            print(f"  Value must be at most {high}.")
            continue
        return value


def get_text(prompt):
    """Keep asking until the user types something (not blank)."""
    while True:
        text = input(prompt).strip()
        if text:
            return text
        print("  This field cannot be empty.")


def get_choice(prompt, options):
    """Ask until the answer matches one of the options (case-insensitive)."""
    lookup = {option.lower(): option for option in options}
    while True:
        text = input(prompt).strip().lower()
        if text in lookup:
            return lookup[text]
        print("  Please choose one of: " + ", ".join(options))


def get_yes_no(prompt):
    """Return True for yes and False for no."""
    while True:
        text = input(prompt + " (y/n): ").strip().lower()
        if text in ("y", "yes"):
            return True
        if text in ("n", "no"):
            return False
        print("  Please type y or n.")


def get_date(prompt):
    """Read a date as YYYY-MM-DD. Pressing Enter gives today's date."""
    while True:
        text = input(prompt + " [YYYY-MM-DD, Enter = today]: ").strip()
        if text == "":
            return date.today()
        try:
            return datetime.strptime(text, "%Y-%m-%d").date()
        except ValueError:
            print("  Invalid date. Example of a valid date: 2026-11-15")


def money(amount):
    """Format a number as rupees, e.g. Rs. 1,250.50"""
    return f"Rs. {amount:,.2f}"
