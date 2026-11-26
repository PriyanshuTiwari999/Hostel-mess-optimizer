"""main.py - Hostel Mess Budget and Nutrition Optimizer (menu-driven program).

Run with:  python main.py
"""
from datetime import date

import budget_tracker
import data_manager
import nutrition_analysis
import optimizer
import report_generator
from utils import get_choice, get_date, get_number, get_text, get_yes_no, money

CATEGORIES = ["Main", "Side", "Beverage", "Staple", "Dal", "Curry", "Snack"]
MEALS = ["Breakfast", "Lunch", "Dinner", "Snack"]
EXPENSE_CATEGORIES = ["Vegetables", "Grains & Pulses", "Dairy", "Egg & Meat", "Gas & Fuel", "Wages & Other"]


def daily_budget(settings):
    return settings["monthly_budget_per_student"] / 30


# ---------------------------------------------------------------- menu actions
def view_foods(foods):
    print(f"\n{'No.':<4}{'Name':<27}{'Category':<10}{'Diet':<5}{'Rs.':>5}{'kcal':>6}{'Prot': >6}{'Fat':>5}")
    print("-" * 68)
    for number, food in enumerate(sorted(foods, key=lambda f: (f["category"], f["name"])), start=1):
        print(f"{number:<4}{food['name']:<27}{food['category']:<10}{food['diet']:<5}"
              f"{food['cost']:>5.0f}{food['calories']:>6.0f}{food['protein']:>6.0f}{food['fat']:>5.0f}")
    print(f"\nTotal items: {len(foods)}   (V = vegetarian, N = non-vegetarian)")


def add_food(foods):
    print("\n--- Add a new food item ---")
    name = get_text("Name: ")
    if any(f["name"].lower() == name.lower() for f in foods):
        print("  This item already exists. Nothing added.")
        return
    category = get_choice(f"Category ({'/'.join(CATEGORIES)}): ", CATEGORIES)
    meal = get_choice(f"Meal ({'/'.join(MEALS)}): ", MEALS)
    diet = get_choice("Diet (V = veg, N = non-veg): ", ["V", "N"])
    food = {
        "name": name, "category": category, "meals": {meal}, "diet": diet,
        "cost": get_number("Cost per serving (Rs.): ", float, 0.5, 1000),
        "calories": get_number("Calories (kcal): ", float, 0, 3000),
        "protein": get_number("Protein (g): ", float, 0, 200),
        "carbs": get_number("Carbohydrates (g): ", float, 0, 500),
        "fat": get_number("Fat (g): ", float, 0, 300),
    }
    foods.append(food)
    data_manager.save_food(food)
    print(f"  '{name}' saved to food_items.csv.")


def rank_menu(foods, settings):
    print("\n--- Rank foods by value ---")
    for key, (label, _) in nutrition_analysis.RANK_CRITERIA.items():
        print(f"  {key}. {label}")
    choice = get_choice("Choose criterion (1-3): ", list(nutrition_analysis.RANK_CRITERIA))
    top_n = get_number("How many items to show (1-20): ", int, 1, 20)
    label, ranked = nutrition_analysis.rank_foods(foods, choice, settings["diet"])
    print(f"\nTop {top_n} by {label}")
    print("-" * 62)
    for position, food in enumerate(ranked[:top_n], start=1):
        print(f"{position:>2}. {food['name']:<27} Rs.{food['cost']:>4.0f}  "
              f"{food['protein'] / food['cost']:>5.2f} g/Rs.  {food['calories'] / food['cost']:>5.1f} kcal/Rs.")


def today_menu(foods, settings):
    budget = daily_budget(settings)
    if get_yes_no(f"Use the default daily budget of {money(budget)} per student?") is False:
        budget = get_number("Enter daily budget per student (Rs.): ", float, 1, 5000)
    plan = optimizer.build_daily_plan(foods, budget, settings["calorie_target"],
                                      settings["protein_target"], settings["diet"])
    show_plan(plan, "OPTIMIZED DAILY MENU", settings, budget)


def show_plan(plan, title, settings, budget):
    if plan is None:
        print("  Cannot build a menu: some meal slot has no food items. Add more items first .")
        return
    cal_t, prot_t = settings["calorie_target"], settings["protein_target"]
    if not plan["feasible"]:
        print(f"\n  The cheapest possible menu costs {money(plan['cost'])}, which is above the "
              f"budget of {money(budget)}. Increase the budget or add cheaper items.")
        return
    print("\n" + report_generator.format_plan(plan, title, cal_t, prot_t, budget))
    if optimizer.targets_met(plan, cal_t, prot_t):
        print(f"Result: all nutrition targets met. Money left unspent: {money(budget - plan[ 'cost'])}")
    else:
        print("Result: budget is too low to meet every target. Missing: ", end="")
        missing = []
        if plan["calories"] < 0.9 * cal_t:
            missing.append(f"{cal_t - plan['calories']:.0f} kcal")
        if plan["protein"] < prot_t:
            missing.append(f"{prot_t - plan['protein']:.0f} g protein")
        print(", ".join(missing) or "calories slightly outside the 90-110% range")


def weekly_menu(foods, settings):
    budget = daily_budget(settings)
    week = optimizer.build_weekly_plan(foods, budget, settings["calorie_target"],
                                       settings["protein_target"], settings["diet"])
    if not week or not week[0]["feasible"]:
        print(f"  Cannot build the weekly menu within {money(budget)} per day.")
        return None
    print(f"\n{'Day':<11}{'Breakfast':<22}{'Lunch (staple + dal)':<34}{'Rs.':>5}{'kcal':>6}{ 'Prot':>6}")
    print("-" * 84)
    for plan in week:
        names = {slot: food["name"] for slot, food in plan["items"]}
        lunch = names[("Lunch", "Staple")].split(" (")[0] + " + " + names[("Lunch", "Dal")]
        print(f"{plan['day']:<11}{names[('Breakfast', 'Main')][:20]:<22}{lunch[:32]:<34}"
              f"{plan['cost']:>5.0f}{plan['calories']:>6.0f}{plan['protein']:>6.0f}")
    total = sum(p["cost"] for p in week)
    print("-" * 84)
    print(f"Weekly cost per student: {money(total)}  |  for {settings['students']} students: "
          f"{money(total * settings['students'])}")
    return week


def compare_scenarios(foods, settings):
    cal_t, prot_t = settings["calorie_target"], settings["protein_target"]
    base = daily_budget(settings)
    budgets = [round(base * f) for f in (0.8, 0.9, 1.0, 1.2)]
    print("\n--- Budget scenarios (daily, per student) ---")
    print(f"{'Budget':>8}{'Cost':>8}{'kcal':>8}{'Protein':>9}  Status")
    print("-" * 56)
    for budget, plan in optimizer.compare_budgets(foods, budgets, cal_t, prot_t, settings["diet"]):
        if plan is None or not plan["feasible"]:
            minimum = f"{plan['cost']:.0f}" if plan else "-"
            print(f"{budget:>8}{minimum:>8}{'-':>8}{'-':>9}  Not possible (cheapest menu costs Rs. {minimum})")
        else:
            status = "Targets met" if optimizer.targets_met(plan, cal_t, prot_t) else "Targets NOT met"
            print(f"{budget:>8}{plan['cost']:>8.0f}{plan['calories']:>8.0f}{plan['protein']: >9.0f}  {status}")
    print("\n--- Vegetarian vs any diet at the default budget ---")
    for diet in ("veg", "any"):
        plan = optimizer.build_daily_plan(foods, base, cal_t, prot_t, diet)
        if plan and plan["feasible"]:
            print(f"{diet:>4}: cost {plan['cost']:.0f}, {plan['calories']:.0f} kcal, {plan['protein']:.0f} g protein")


def analyse_my_day(foods, settings):
    print("\nType the foods eaten today, separated by commas")
    print("Example: Poha, Banana, Tea, Roti, Dal Tadka, Aloo Gobhi")
    names = [n for n in get_text("Foods: ").split(",") if n.strip()]
    budget = daily_budget(settings)
    matched, unknown, totals, advice = nutrition_analysis.analyse_meal(
        foods, names, budget, settings["calorie_target"], settings["protein_target"])
    if unknown:
        print("  Not found in database: " + ", ".join(unknown))
    if not matched:
        print("  No valid food items to analyse.")
        return
    print(f"\nMatched: {', '.join(f['name'] for f in matched)}")
    print(f"Cost {totals['cost']:.0f} Rs. | {totals['calories']:.0f} kcal | "
          f"{totals['protein']:.0f} g protein | {totals['fat']:.0f} g fat")
    for line in advice:
        print(" *", line)


def record_expense():
    print("\n--- Record a mess expense ---")
    expense_date = get_date("Date")
    category = get_choice(f"Category ({', '.join(EXPENSE_CATEGORIES)}): ", EXPENSE_CATEGORIES)
    amount = get_number("Amount (Rs.): ", float, 1, 10_000_000)
    note = input("Note (optional): ").strip().replace(",", " ")
    data_manager.add_expense(expense_date, category, amount, note)
    print("  Expense saved.")


def monthly_summary(settings, save_chart=False):
    expenses = data_manager.load_expenses()
    year = get_number("Year (e.g. 2026): ", int, 2000, 2100)
    month = get_number("Month (1-12): ", int, 1, 12)
    s = budget_tracker.summarize_month(expenses, year, month, settings["students"],
                                       settings["monthly_budget_per_student"])
    if s is None:
        print("  No expenses recorded for that month.")
        return
    print(f"\nMONTHLY BUDGET SUMMARY  {year}-{month:02d}")
    print("-" * 60)
    print(f"Monthly budget        : {money(s['budget'])}")
    print(f"Spent so far          : {money(s['total'])}  ({s['percent_used']:.1f}% used, "
          f"day {s['days_elapsed']} of {s['days_in_month']})")
    print(f"Projected month total : {money(s['projected'])}")
    print(f"Cost per student/day  : {money(s['actual_per_student_day'])} actual vs "
          f"{money(s['planned_per_student_day'])} planned")
    print(f"Highest spending day  : {s['peak_day']} ({money(s['peak_amount'])})")
    print("\nSpending by category:")
    for category, amount in sorted(s["by_category"].items(), key=lambda x: x[1], reverse=True):
        print(f"  {category:<18}{money(amount):>18}  {amount / s['total'] * 100:>5.1f}%")
    print("\nAlerts:")
    for alert in s["alerts"]:
        print(" !", alert)
    if save_chart and report_generator.plot_expenses(s, "expense_chart.png"):
        print("\nChart saved as expense_chart.png")


def save_reports(foods, settings):
    week = weekly_menu(foods, settings)
    if not week:
        return
    report_generator.save_weekly_report(week, settings, "weekly_menu_report.txt")
    print("\nSaved: weekly_menu_report.txt")
    if report_generator.plot_weekly(week, daily_budget(settings), "weekly_plan_chart.png"):
        print("Saved: weekly_plan_chart.png")
    else:
        print("(Install matplotlib to also get the chart: pip install matplotlib)")
    if get_yes_no("Also create the expense chart?"):
        monthly_summary(settings, save_chart=True)


def change_settings(settings):
    print("\n--- Settings (press Enter to keep the current value) ---")
    prompts = [("students", int, 1, 5000, "Number of students"),
               ("monthly_budget_per_student", float, 500, 20000, "Monthly budget per student (Rs.)"),
               ("calorie_target", float, 1200, 4500, "Calorie target per day (kcal)"),
               ("protein_target", float, 20, 250, "Protein target per day (g)")]
    for key, kind, low, high, label in prompts:
        while True:
            text = input(f"{label} [{settings[key]}]: ").strip()
            if text == "":
                break
            try:
                value = kind(text)
            except ValueError:
                print("  Invalid number.")
                continue
            if low <= value <= high:
                settings[key] = value
                break
            print(f"  Value must be between {low} and {high}.")
    settings["diet"] = get_choice(f"Diet (any/veg) [{settings['diet']}]: ", ["any", "veg"])
    data_manager.save_settings(settings)
    print("  Settings saved.")


# ------------------------------------------------------------------- main loop
MENU = """
==================== HOSTEL MESS BUDGET & NUTRITION OPTIMIZER ====================
 1. View food database          7. Analyse what I ate today
 2. Add a new food item         8. Record a mess expense
 3. Rank foods by value         9. Monthly budget summary & alerts
 4. Optimized menu for today   10. Save weekly report & charts
 5. Optimized weekly menu      11. Change settings
 6. Compare budget scenarios    0. Exit
==================================================================================="""


def main():
    foods = data_manager.load_foods()
    settings = data_manager.load_settings()
    if not foods:
        print("No food data available. Please check food_items.csv.")
        return
    while True:
        print(MENU)
        print(f"Diet: {settings['diet']} | Targets: {settings['calorie_target']:.0f} kcal, "
              f"{settings['protein_target']:.0f} g protein | Budget: {money(daily_budget(settings))}/student/day")
        try:
            choice = input("Enter your choice (0-11): ").strip()
            if choice == "1":
                view_foods(foods)
            elif choice == "2":
                add_food(foods)
            elif choice == "3":
                rank_menu(foods, settings)
            elif choice == "4":
                today_menu(foods, settings)
            elif choice == "5":
                weekly_menu(foods, settings)
            elif choice == "6":
                compare_scenarios(foods, settings)
            elif choice == "7":
                analyse_my_day(foods, settings)
            elif choice == "8":
                record_expense()
            elif choice == "9":
                monthly_summary(settings)
            elif choice == "10":
                save_reports(foods, settings)
            elif choice == "11":
                change_settings(settings)
            elif choice == "0":
                print("Thank you for using the Mess Optimizer. Goodbye!")
                break
            else:
                print("  Invalid choice. Please enter a number from 0 to 11.")
        except (EOFError, KeyboardInterrupt):
            print("\nExiting. Goodbye!")
            break


if __name__ == "__main__":
    main()
