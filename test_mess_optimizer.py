"""test_mess_optimizer.py - simple automated tests. Run with:  python test_mess_optimizer.py """
from datetime import date

import budget_tracker
import data_manager
import nutrition_analysis
import optimizer

foods = data_manager.load_foods()
CAL, PROT = 2300.0, 70.0


def test_normal_plan_meets_targets():
    plan = optimizer.build_daily_plan(foods, 110, CAL, PROT)
    assert plan["feasible"] and plan["cost"] <= 110
    assert optimizer.targets_met(plan, CAL, PROT)


def test_budget_below_minimum_is_infeasible():
    cheapest_plan = optimizer.build_daily_plan(foods, 0, CAL, PROT)
    assert cheapest_plan is not None
    minimum_cost = cheapest_plan["cost"]
    plan = optimizer.build_daily_plan(foods, minimum_cost - 0.01, CAL, PROT)
    assert plan is not None and plan["feasible"] is False


def test_boundary_budget_equal_to_cheapest_menu():
    cheapest_plan = optimizer.build_daily_plan(foods, 10000, CAL, PROT)
    assert cheapest_plan is not None
    cheapest = cheapest_plan["cost"]
    plan = optimizer.build_daily_plan(foods, cheapest, CAL, PROT)
    assert plan is not None and plan["feasible"] and plan["cost"] <= cheapest


def test_veg_plan_has_no_nonveg_items():
    plan = optimizer.build_daily_plan(foods, 110, CAL, PROT, diet="veg")
    assert all(food["diet"] == "V" for _, food in plan["items"])


def test_no_food_repeats_within_a_day():
    plan = optimizer.build_daily_plan(foods, 110, CAL, PROT)
    names = [food["name"] for _, food in plan["items"]]
    assert len(names) == len(set(names))


def test_weekly_plan_has_seven_days_within_budget():
    week = optimizer.build_weekly_plan(foods, 110, CAL, PROT)
    assert len(week) == 7 and all(day["cost"] <= 110 for day in week)


def test_score_is_zero_when_targets_met():
    plan = optimizer.build_daily_plan(foods, 110, CAL, PROT)
    assert plan["score"] == 0


def test_find_food_partial_and_unknown():
    assert nutrition_analysis.find_food(foods, "dal tadka")["name"] == "Dal Tadka"
    assert nutrition_analysis.find_food(foods, "pizza") is None


def test_analyse_meal_low_protein_advice():
    _, unknown, totals, advice = nutrition_analysis.analyse_meal(foods, ["Tea", "Banana"], 110, CAL, PROT)
    assert unknown == [] and any("Protein is low" in a for a in advice)


def test_ranking_orders_by_protein_per_rupee():
    _, ranked = nutrition_analysis.rank_foods(foods, "1")
    values = [f["protein"] / f["cost"] for f in ranked]
    assert values == sorted(values, reverse=True)


def test_budget_alert_when_projected_overspend():
    expenses = [{"date": date(2026, 11, d), "category": "Vegetables", "amount": 30000.0, "note": ""}
                for d in range(1, 11)]
    summary = budget_tracker.summarize_month(expenses, 2026, 11, 200, 3300)
    assert any("over budget" in alert for alert in summary["alerts"])


def test_empty_month_returns_none():
    assert budget_tracker.summarize_month([], 2026, 11, 200, 3300) is None


if __name__ == "__main__":
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_" )]
    passed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS  {name}")
            passed += 1
        except AssertionError:
            print(f"FAIL  {name}")
    print(f"\n{passed} of {len(tests)} tests passed")
