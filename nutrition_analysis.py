"""nutrition_analysis.py - ranking foods by value and analysing a meal the user has eaten."""
from optimizer import sum_nutrients, FAT_SHARE, CALORIE_UPPER

RANK_CRITERIA = {
    "1": ("Protein per rupee (g/Rs.)", lambda f: f["protein"] / f["cost"]),
    "2": ("Calories per rupee (kcal/Rs.)", lambda f: f["calories"] / f["cost"]),
    "3": ("Lowest cost first (Rs.)", lambda f: -f["cost"]),
}


def rank_foods(foods, criterion_key, diet="any"):
    """Return foods sorted from best to worst according to the chosen criterion."""
    label, key_function = RANK_CRITERIA[criterion_key]
    pool = [f for f in foods if diet == "any" or f["diet"] == "V"]
    return label, sorted(pool, key=key_function, reverse=True)


def find_food(foods, text):
    """Find a food by name: exact match first, then partial match (case-insensitive)."""
    text = text.strip().lower()
    for food in foods:
        if food["name"].lower() == text:
            return food
    for food in foods:
        if text and text in food["name"].lower():
            return food
    return None


def analyse_meal(foods, names, budget, calorie_target, protein_target):
    """Compare what a student ate in a day with the targets.
    Returns (matched foods, unknown names, totals, list of advice strings)."""
    matched, unknown = [], []
    for name in names:
        food = find_food(foods, name)
        if food is None:
            unknown.append(name)
        else:
            matched.append(food)

    totals = sum_nutrients(matched)
    advice = []
    if matched:
        if totals["calories"] < 0.90 * calorie_target:
            advice.append(f"Calories are low ({totals['calories']:.0f} of {calorie_target:.0f} kcal). "
                          "Add a staple such as rice or roti.")
        elif totals["calories"] > CALORIE_UPPER * calorie_target:
            advice.append("Calories are above 110% of the target. Reduce fried items or large portions.")
        if totals["protein"] < protein_target:
            eaten = {f["name"] for f in matched}
            best = [f for f in rank_foods(foods, "1")[1] if f["name"] not in eaten][:3]
            names_text = ", ".join(f["name"] for f in best)
            advice.append(f"Protein is low ({totals['protein']:.0f} of {protein_target:.0f} g). "
                          f"Best-value protein options: {names_text}.")
        max_fat = FAT_SHARE * calorie_target / 9
        if totals["fat"] > max_fat:
            advice.append(f"Fat is high ({totals['fat']:.0f} g; limit about {max_fat:.0f} g) . "
                          "Choose boiled or steamed items instead of fried ones.")
        if totals["cost"] > budget:
            advice.append(f"Cost (Rs. {totals['cost']:.0f}) is above the daily budget (Rs. { budget:.0f}).")
        if not advice:
            advice.append("Well balanced! All targets are met within the budget.")
    return matched, unknown, totals, advice
