"""budget_tracker.py - monthly mess expense summary, projection and rule-based alerts."""
import calendar


def summarize_month(expenses, year, month, students, monthly_budget_per_student):
    """Analyse the expenses of one month. Returns a dictionary, or None if there is no data. """
    rows = [e for e in expenses if e["date"].year == year and e["date"].month == month]
    if not rows:
        return None

    total = sum(e["amount"] for e in rows)
    by_category, by_day = {}, {}
    for e in rows:
        by_category[e["category"]] = by_category.get(e["category"], 0.0) + e["amount"]
        by_day[e["date"]] = by_day.get(e["date"], 0.0) + e["amount"]

    days_in_month = calendar.monthrange(year, month)[1]
    days_elapsed = max(d.day for d in by_day)              # last day with a record
    budget = students * monthly_budget_per_student
    projected = total / days_elapsed * days_in_month
    peak_day = max(by_day, key=by_day.get)

    summary = {
        "year": year, "month": month, "total": total, "budget": budget,
        "percent_used": total / budget * 100,
        "days_elapsed": days_elapsed, "days_in_month": days_in_month,
        "projected": projected,
        "actual_per_student_day": total / (students * days_elapsed),
        "planned_per_student_day": monthly_budget_per_student / days_in_month,
        "by_category": by_category, "peak_day": peak_day, "peak_amount": by_day[peak_day],
    }
    summary["alerts"] = make_alerts(summary)
    return summary


def make_alerts(s):
    """Simple rule-based alerts."""
    alerts = []
    month_elapsed_pct = s["days_elapsed"] / s["days_in_month"] * 100
    if s["percent_used"] >= 100:
        alerts.append("CRITICAL: The monthly budget has already been exceeded.")
    elif s["projected"] > s["budget"]:
        over = s["projected"] - s["budget"]
        alerts.append(f"WARNING: At the current rate the month will end Rs. {over:,.0f} over budget.")
    if s["percent_used"] > month_elapsed_pct + 10 and s["percent_used"] < 100:
        alerts.append(f"WARNING: {s['percent_used']:.0f}% of the budget is used but only "
                      f"{month_elapsed_pct:.0f}% of the month has passed.")
    for category, amount in sorted(s["by_category"].items(), key=lambda x: x[1], reverse=True):
        share = amount / s["total"] * 100
        if share > 35:
            alerts.append(f"NOTE: '{category}' takes {share:.0f}% of all spending (limit 35% ). Check for savings.")
    if not alerts:
        alerts.append("OK: Spending is on track for the month.")
    return alerts
