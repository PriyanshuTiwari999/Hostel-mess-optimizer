"""data_manager.py - reads and writes all TXT / CSV files (food items, settings, expenses)."""
import csv
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FOOD_FILE = os.path.join(BASE_DIR, "food_items.csv")
EXPENSE_FILE = os.path.join(BASE_DIR, "expenses.csv")
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.txt")

FOOD_FIELDS = ["name", "category", "meal", "diet", "cost", "calories", "protein", "carbs", "fat"]
NUMERIC_FIELDS = ["cost", "calories", "protein", "carbs", "fat"]

DEFAULT_SETTINGS = {
    "students": 200,                       # students eating in the mess
    "monthly_budget_per_student": 3300.0,  # Rs. per student per month
    "calorie_target": 2300.0,              # kcal per student per day
    "protein_target": 70.0,                # grams per student per day
    "diet": "any",                         # "any" or "veg"
}


# ------------------------------------------------------------------ food items
def load_foods():
    """Read food_items.csv and return a list of dictionaries. Bad rows are skipped."""
    foods = []
    try:
        with open(FOOD_FILE, newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for line_no, row in enumerate(reader, start=2):
                try:
                    food = {
                        "name": row["name"].strip(),
                        "category": row["category"].strip(),
                        "meals": {m.strip() for m in row["meal"].split("|")},  # a set
                        "diet": row["diet"].strip().upper(),
                    }
                    for field in NUMERIC_FIELDS:
                        food[field] = float(row[field])
                        if food[field] < 0:
                            raise ValueError("negative value")
                    if food["name"] == "" or food["cost"] <= 0 or food["diet"] not in ("V", "N"):
                        raise ValueError("invalid data")
                    foods.append(food)
                except (KeyError, ValueError, AttributeError):
                    print(f"  Warning: skipped invalid row {line_no} in food_items.csv")
    except FileNotFoundError:
        print("  Error: food_items.csv was not found.")
    return foods


def save_food(food):
    """Append one new food item to food_items.csv."""
    new_file = not os.path.exists(FOOD_FILE)
    with open(FOOD_FILE, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if new_file:
            writer.writerow(FOOD_FIELDS)
        writer.writerow([
            food["name"], food["category"], "|".join(sorted(food["meals"])), food["diet"],
            food["cost"], food["calories"], food["protein"], food["carbs"], food["fat"],
        ])


# -------------------------------------------------------------------- settings
def load_settings():
    """Read settings.txt (key=value lines). Missing or bad values fall back to defaults."""
    settings = dict(DEFAULT_SETTINGS)
    try:
        with open(SETTINGS_FILE, encoding="utf-8") as file:
            for line in file:
                if "=" not in line:
                    continue
                key, value = line.strip().split("=", 1)
                if key in settings:
                    try:
                        settings[key] = type(DEFAULT_SETTINGS[key])(value)
                    except ValueError:
                        pass
    except FileNotFoundError:
        save_settings(settings)
    return settings


def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as file:
        for key, value in settings.items():
            file.write(f"{key}={value}\n")


# -------------------------------------------------------------------- expenses
def load_expenses():
    """Return a list of expense dictionaries: date, category, amount, note."""
    expenses = []
    try:
        with open(EXPENSE_FILE, newline="", encoding="utf-8") as file:
            for line_no, row in enumerate(csv.DictReader(file), start=2):
                try:
                    expenses.append({
                        "date": datetime.strptime(row["date"], "%Y-%m-%d").date(),
                        "category": row["category"].strip(),
                        "amount": float(row["amount"]),
                        "note": row.get("note", ""),
                    })
                except (KeyError, ValueError):
                    print(f"  Warning: skipped invalid row {line_no} in expenses.csv")
    except FileNotFoundError:
        pass  # no expenses recorded yet
    return expenses


def add_expense(expense_date, category, amount, note):
    new_file = not os.path.exists(EXPENSE_FILE)
    with open(EXPENSE_FILE, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if new_file:
            writer.writerow(["date", "category", "amount", "note"])
        writer.writerow([expense_date.isoformat(), category, amount, note])
