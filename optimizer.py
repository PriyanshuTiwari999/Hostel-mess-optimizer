"""optimizer.py - the core computational feature.

Builds a daily / weekly mess menu that gets as close as possible to the calorie and
protein targets without crossing the budget.  Method: greedy local search.
  1. Pick the cheapest food for every meal slot (the "minimum cost" menu).
  2. Repeatedly try replacing ONE item with another item of the same slot.
  3. Take the replacement that reduces the nutrition penalty the most per extra rupee,
     as long as the total stays inside the budget.
  4. Stop when no replacement improves the menu.
"""

# A slot is a tuple (meal, category). One food is chosen for each slot every day.
SLOTS = [
    ("Breakfast", "Main"), ("Breakfast", "Side"), ("Breakfast", "Beverage"),
    ("Lunch", "Staple"), ("Lunch", "Dal"), ("Lunch", "Curry"),
    ("Snack", "Snack"),
    ("Dinner", "Staple"), ("Dinner", "Dal"), ("Dinner", "Curry"), ("Dinner", "Side"),
]

WEEK_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

PROTEIN_WEIGHT = 2.0   # missing protein is punished twice as much as missing calories
CALORIE_UPPER = 1.10   # calories above 110 % of the target are also penalised
FAT_SHARE = 0.30       # fat should not give more than 30 % of the calories


def sum_nutrients(foods):
    """Add up cost and nutrients of a list of foods."""
    totals = {"cost": 0.0, "calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}
    for food in foods:
        for key in totals:
            totals[key] += food[key]
    return totals


def plan_score(foods, calorie_target, protein_target):
    """Penalty score of a menu. 0 means all targets are satisfied; lower is better."""
    t = sum_nutrients(foods)
    score = 0.0
    if t["calories"] < calorie_target:
        score += (calorie_target - t["calories"]) / calorie_target
    elif t["calories"] > CALORIE_UPPER * calorie_target:
        score += (t["calories"] - CALORIE_UPPER * calorie_target) / calorie_target
    if t["protein"] < protein_target:
        score += PROTEIN_WEIGHT * (protein_target - t["protein"]) / protein_target
    max_fat = FAT_SHARE * calorie_target / 9          # 1 g fat = 9 kcal
    if t["fat"] > max_fat:
        score += (t["fat"] - max_fat) / max_fat
    return score


def get_candidates(foods, slot, diet, avoid_names=None):
    """All foods that can fill a slot (matching meal, category and diet)."""
    meal, category = slot
    options = [f for f in foods
               if meal in f["meals"] and f["category"] == category
               and (diet == "any" or f["diet"] == "V")]
    if avoid_names:                                  # variety rule: skip recently served items
        different = [f for f in options if f["name"] not in avoid_names]
        if different:
            options = different
    return options


def build_daily_plan(foods, budget, calorie_target, protein_target, diet="any", avoid=None):
    """Return a plan dictionary:
         items     - list of (slot, food)
         feasible  - False if even the cheapest menu is above the budget
         cost, calories, protein, carbs, fat, score
       or None if some slot has no food at all."""
    avoid = avoid or {}
    candidates = {}
    for slot in SLOTS:
        options = get_candidates(foods, slot, diet, avoid.get(slot))
        if not options:
            return None
        candidates[slot] = options

    # Step 1: cheapest menu (no food repeated within the same day)
    chosen, used = {}, set()
    for slot in SLOTS:
        for food in sorted(candidates[slot], key=lambda f: f["cost"]):
            if food["name"] not in used:
                chosen[slot] = food
                used.add(food["name"])
                break
        else:
            return None
    cost = sum_nutrients(chosen.values())["cost"]
    feasible = cost <= budget

    # Steps 2-4: improve the menu while there is budget left
    while feasible:
        current = plan_score(chosen.values(), calorie_target, protein_target)
        best_move, best_ratio = None, 0.0
        for slot in SLOTS:
            for food in candidates[slot]:
                if food["name"] in used:
                    continue
                new_cost = cost - chosen[slot]["cost"] + food["cost"]
                if new_cost > budget:
                    continue
                trial = dict(chosen)
                trial[slot] = food
                gain = current - plan_score(trial.values(), calorie_target, protein_target)
                if gain <= 1e-9:
                    continue
                extra = max(food["cost"] - chosen[slot]["cost"], 1.0)
                if gain / extra > best_ratio:
                    best_ratio, best_move = gain / extra, (slot, food)
        if best_move is None:
            break
        slot, food = best_move
        used.discard(chosen[slot]["name"])
        cost += food["cost"] - chosen[slot]["cost"]
        chosen[slot] = food
        used.add(food["name"])

    plan = sum_nutrients(chosen.values())
    plan["items"] = [(slot, chosen[slot]) for slot in SLOTS]
    plan["feasible"] = feasible
    plan["score"] = plan_score(chosen.values(), calorie_target, protein_target)
    return plan


def targets_met(plan, calorie_target, protein_target):
    """True when calories are within 90-110 % of target and protein is at least the target."""
    return (0.90 * calorie_target <= plan["calories"] <= CALORIE_UPPER * calorie_target
            and plan["protein"] >= protein_target)


def build_weekly_plan(foods, budget, calorie_target, protein_target, diet="any"):
    """Seven daily plans. A slot avoids items served in the previous two days (if the budget allows)."""
    week, history = [], []
    for day in WEEK_DAYS:
        plan = None
        # Variety is a soft rule: try avoiding the last 2 days, then the last day, then nothing.
        # The budget is a hard rule: a plan above the budget is never accepted.
        for window in (2, 1, 0):
            recent = history[-window:] if window else []
            avoid = {slot: {past[slot] for past in recent} for slot in SLOTS}
            plan = build_daily_plan(foods, budget, calorie_target, protein_target, diet, avoid)
            if plan is not None and plan["feasible"]:
                break
        if plan is None:
            return []
        plan["day"] = day
        week.append(plan)
        history.append({slot: food["name"] for slot, food in plan["items"]})
    return week


def compare_budgets(foods, budgets, calorie_target, protein_target, diet="any"):
    """Build one daily plan for each budget so the trade-off can be compared."""
    results = []
    for budget in budgets:
        plan = build_daily_plan(foods, budget, calorie_target, protein_target, diet)
        results.append((budget, plan))
    return results
